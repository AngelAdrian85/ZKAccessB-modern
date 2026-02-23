from __future__ import annotations

import json
import os
from collections import Counter


def main() -> int:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zkeco_config.settings")

    import django

    django.setup()

    from agent.models import (
        AccessLevel,
        AuditLog,
        CommandLog,
        Device,
        DeviceEventLog,
        DeviceRealtimeLog,
        Door,
        Employee,
    )

    device_id = int(os.environ.get("PIPE_DEVICE_ID") or 22)

    print("=== Device ===")
    dev = Device.objects.filter(id=device_id).first()
    if not dev:
        print({"error": "device_not_found", "device_id": device_id})
        return 2

    print(
        {
            "id": dev.id,
            "name": dev.name,
            "sn": dev.serial_number,
            "ip": str(dev.ip_address or ""),
            "port": int(dev.port or 0),
            "enabled": bool(dev.enabled),
            "comm_password_set": bool((dev.comm_password or "").strip()),
            "last_contact": dev.last_contact.isoformat() if dev.last_contact else None,
        }
    )

    print("\n=== DB Personnel (syncability snapshot) ===")
    try:
        total_emp = Employee.objects.count()
        active_emp = Employee.objects.filter(active=True).count()
        active_with_card = (
            Employee.objects.filter(active=True)
            .exclude(card_number__isnull=True)
            .exclude(card_number="")
            .count()
        )

        device_doors = Door.objects.filter(device_id=int(dev.id)).exclude(door_number__isnull=True)
        device_levels = AccessLevel.objects.filter(doors__in=device_doors).distinct()
        device_emp = Employee.objects.filter(active=True, access_levels__in=device_levels).distinct()
        device_emp_count = device_emp.count()
        device_emp_with_card = device_emp.exclude(card_number__isnull=True).exclude(card_number="").count()

        print(
            {
                "employees_total": total_emp,
                "employees_active": active_emp,
                "active_with_card_number": active_with_card,
                "device_doors": device_doors.count(),
                "device_access_levels": device_levels.count(),
                "device_sync_employees": device_emp_count,
                "device_sync_employees_with_card": device_emp_with_card,
            }
        )
    except Exception as e:
        print({"error": f"{type(e).__name__}: {e}"})

    # ------------------------------------------------------------
    # Direct controller probe (pull-mode) via plcommpro bridge
    # ------------------------------------------------------------
    print("\n=== Controller Probe (plcommpro bridge) ===")
    try:
        from agent.plcommpro_bridge import PlcommproConnInfo, query_data

        conn = PlcommproConnInfo(
            ipaddress=str(dev.ip_address or ""),
            ip_port=int(dev.port or 4370),
            password=str(dev.comm_password or ""),
            timeout=3000,
            protocol="TCP",
        )

        def _preview(label: str, resp: dict, max_lines: int = 8):
            ok = bool(resp.get("ok"))
            result = resp.get("result")
            last_error = resp.get("last_error")
            data = str(resp.get("data") or "")
            data = data.replace("\x00", "")
            lines = [ln for ln in data.split("\r\n") if ln]
            head = "\n".join(lines[:max_lines])
            if len(lines) > max_lines:
                head += f"\n... ({len(lines)} lines total)"
            print({"label": label, "ok": ok, "result": result, "last_error": last_error})
            print(head or "(empty)")

        # NewRecord transaction (near-realtime)
        _preview(
            "transaction NewRecord",
            query_data(conn, table="transaction", fields="*", option="NewRecord"),
        )
        # RTLOG table if present
        _preview(
            "rtlog (full)",
            query_data(conn, table="rtlog", fields="*"),
        )
        # Transaction full (limited preview)
        _preview(
            "transaction (full)",
            query_data(conn, table="transaction", fields="*"),
        )
    except Exception as e:
        print({"probe": "skipped", "reason": f"{type(e).__name__}: {e}"})

    print("\n=== DeviceRealtimeLog (lookback) ===")
    lookback = 800
    rows = list(DeviceRealtimeLog.objects.filter(device_id=device_id).order_by("-id")[:lookback])
    rows.reverse()

    headers = 0
    rows9 = 0
    normalized_like = 0
    card_hits = 0
    unique_cards = set()

    for r in rows:
        raw = (r.raw or "").strip()
        low = raw.lower()
        parts = [p.strip() for p in raw.split(",")]

        if low.startswith("pin,verified,doorid"):
            headers += 1

        # Headerless transaction rows often show as 9 comma-separated fields.
        if len(parts) == 9 and parts[0].isdigit() and parts[1].isdigit():
            rows9 += 1
            cardno = parts[7].strip() if len(parts) > 7 else ""
            if cardno:
                card_hits += 1
                unique_cards.add(cardno)

        # Normalized shape: ts,pin,card,door,event,verified
        if len(parts) >= 6 and "-" in parts[0] and ":" in parts[0]:
            normalized_like += 1
            card = parts[2].strip()
            if card:
                card_hits += 1
                unique_cards.add(card)

    sample_first = rows[0].raw[:160] if rows else None
    sample_last = rows[-1].raw[:160] if rows else None

    print(
        {
            "lookback": lookback,
            "rows": len(rows),
            "headers": headers,
            "rows_9_fields": rows9,
            "normalized_like": normalized_like,
            "card_hits": card_hits,
            "unique_cards": sorted(list(unique_cards))[:10],
            "sample_first": sample_first,
            "sample_last": sample_last,
        }
    )

    print("\n=== AuditLog (module=iclock) recent ===")
    auds = list(AuditLog.objects.filter(module="iclock", entity_id=device_id).order_by("-timestamp")[:50])
    action_counts = Counter(a.action for a in auds)
    cards_present_total = 0
    cards_present_max = 0
    latest = auds[0] if auds else None

    for a in auds:
        try:
            det = json.loads(a.details or "{}")
            cp = int(det.get("cards_present") or 0)
            cards_present_total += cp
            cards_present_max = max(cards_present_max, cp)
        except Exception:
            pass

    print(
        {
            "rows": len(auds),
            "actions": dict(action_counts),
            "cards_present_total": cards_present_total,
            "cards_present_max": cards_present_max,
            "latest_action": latest.action if latest else None,
            "latest_ts": latest.timestamp.isoformat() if latest else None,
            "latest_ip": str(latest.ip_address) if latest and latest.ip_address else None,
        }
    )
    if latest:
        print("latest.details=", latest.details)

    print("\n=== CommandLog recent (device) ===")
    cmds = list(CommandLog.objects.filter(device_id=device_id).order_by("-id")[:25])
    cmds.reverse()
    print({"rows": len(cmds)})
    if cmds:
        last = cmds[-1]
        print(
            {
                "latest_id": last.id,
                "latest_status": last.status,
                "latest_command": last.command,
                "latest_result": last.result,
                "latest_executed_at": last.executed_at.isoformat() if last.executed_at else None,
            }
        )

    print("\n=== CommandLog SYNC_PERSONNEL (recent) ===")
    syncs = list(
        CommandLog.objects.filter(device_id=device_id, command__startswith="SYNC_PERSONNEL")
        .order_by("-id")[:10]
    )
    syncs.reverse()
    print({"rows": len(syncs)})
    for s in syncs[-5:]:
        print(
            {
                "id": s.id,
                "status": s.status,
                "executed_at": s.executed_at.isoformat() if s.executed_at else None,
                "result": (s.result or "")[:160],
            }
        )

    print("\n=== DeviceEventLog recent (device) ===")
    evs = list(DeviceEventLog.objects.filter(device_id=device_id).order_by("-id")[:15])
    evs.reverse()
    print({"rows": len(evs)})
    if evs:
        last = evs[-1]
        print(
            {
                "latest_id": last.id,
                "latest_code": last.code,
                "latest_timestamp_str": last.timestamp_str,
                "latest_raw_line": (last.raw_line or "")[:200],
            }
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
