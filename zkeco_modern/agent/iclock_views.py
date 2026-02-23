from __future__ import annotations

import json
import logging
from typing import Dict, Iterable, List, Optional, Tuple

import datetime as _dt

from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


LOG = logging.getLogger(__name__)


def _audit_event(
    *,
    action: str,
    device_id: int,
    entity_name: str,
    details_obj: dict,
    remote_ip: str,
) -> None:
    """Best-effort durable audit trail for device push/poll events.

    Uses existing AuditLog table but keeps writes non-fatal.
    """
    try:
        from agent.models import AuditLog

        details = json.dumps(details_obj or {}, ensure_ascii=False, sort_keys=True)
        # Avoid unbounded growth per request.
        if len(details) > 8000:
            details = details[:8000] + "…"

        AuditLog.objects.create(
            user=None,
            module="iclock",
            action=(action or "")[:32],
            entity_id=int(device_id or 0),
            entity_name=(entity_name or "")[:256] or None,
            details=details,
            ip_address=(remote_ip or None),
        )
    except Exception:
        return


def _casefold_dict(items: Iterable[Tuple[str, str]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in items:
        try:
            kk = str(k or "").strip().lower()
        except Exception:
            kk = ""
        if not kk:
            continue
        out[kk] = str(v or "")
    return out


def _extract_params(request: HttpRequest) -> Dict[str, str]:
    params: Dict[str, str] = {}
    try:
        params.update(_casefold_dict(request.GET.items()))
    except Exception:
        pass
    try:
        params.update(_casefold_dict(request.POST.items()))
    except Exception:
        pass
    return params


def _extract_device_sn(params: Dict[str, str]) -> str:
    for key in (
        "sn",
        "serial",
        "serial_number",
        "devsn",
        "device_sn",
        "devicesn",
    ):
        v = (params.get(key) or "").strip()
        if v:
            return v
    return ""


def _normalize_rtlog_line(line: str) -> Optional[str]:
    raw = (line or "").strip()
    if not raw:
        return None

    low = raw.lower()
    if low == "ok" or low == "ok\n":
        return None

    # Many devices send tab-separated fields; the rest of the system expects comma-separated.
    if "\t" in raw and "," not in raw:
        raw = raw.replace("\t", ",")

    return raw.strip()


def _split_fields(raw: str) -> List[str]:
    # Accept either comma-separated or tab-separated lines.
    if "\t" in raw and "," not in raw:
        return [str(p or "").strip() for p in raw.split("\t")]
    return [str(p or "").strip() for p in raw.split(",")]


def _looks_like_header(fields: List[str]) -> bool:
    low = [str(f or "").strip().lower() for f in (fields or [])]
    if not low:
        return False
    # Common ZK push transaction header.
    must = {"pin", "verified", "doorid", "eventtype"}
    if not must.issubset(set(low)):
        return False
    # Strong indicators
    return ("time_second" in low) or ("cardno" in low)


def _normalize_cdata_payload(lines: List[str]) -> List[str]:
    """Normalize ADMS/iClock 'cdata' payloads.

    Supports both:
      - already-normalized RTLOG (ts,pin,card,door,code,verify,...)
      - ZK transaction table with header:
          Pin,Verified,DoorID,EventType,InOutState,Time_second,Index,Cardno,Sitecode
        followed by data rows.
    """
    out: List[str] = []
    col_idx: Optional[Dict[str, int]] = None

    def _normalize_txn_by_position(fields: List[str]) -> Optional[str]:
        """Normalize headerless ZK transaction rows by column position.

        Expected order (common on C3/F3 panels):
          Pin,Verified,DoorID,EventType,InOutState,Time_second,Index,Cardno,Sitecode

        Returns normalized string: ts,pin,card,door,eventType,verified
        """
        try:
            if len(fields) != 9:
                return None
            # Basic numeric sanity checks to avoid false positives.
            if not (fields[0].strip().lstrip('-').isdigit() and fields[1].strip().lstrip('-').isdigit()):
                return None
            if not (fields[2].strip().isdigit() and fields[3].strip().lstrip('-').isdigit() and fields[5].strip().lstrip('-').isdigit()):
                return None

            pin = str(fields[0] or '').strip()
            verified = str(fields[1] or '').strip()
            door = str(fields[2] or '').strip()
            event_type = str(fields[3] or '').strip()
            card = str(fields[7] or '').strip()
            time_second = str(fields[5] or '').strip()

            ts_str = ''
            try:
                secs = int(float(time_second)) if time_second else 0
                base = _dt.datetime(2000, 1, 1, 0, 0, 0)
                ts = base + _dt.timedelta(seconds=secs)
                ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                ts_str = ''

            norm = f"{ts_str},{pin},{card},{door},{event_type},{verified}"
            return _normalize_rtlog_line(norm)
        except Exception:
            return None

    for ln in lines:
        raw = (ln or "").strip()
        if not raw:
            continue

        fields = _split_fields(raw)

        if _looks_like_header(fields):
            col_idx = {str(name).strip().lower(): i for i, name in enumerate(fields) if str(name or '').strip()}
            continue

        # If we previously saw a header, try to map into normalized RTLOG format.
        if col_idx:
            def _get(key: str) -> str:
                try:
                    i = int(col_idx.get(key, -1))
                except Exception:
                    i = -1
                if i < 0 or i >= len(fields):
                    return ""
                return str(fields[i] or "").strip()

            pin = _get("pin")
            verified = _get("verified")
            door = _get("doorid")
            event_type = _get("eventtype")
            card = _get("cardno")
            time_second = _get("time_second")

            ts_str = ""
            try:
                secs = int(float(time_second)) if time_second else 0
                # ZK often uses seconds since 2000-01-01.
                base = _dt.datetime(2000, 1, 1, 0, 0, 0)
                ts = base + _dt.timedelta(seconds=secs)
                ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                ts_str = ""

            # Standard shape expected by monitor parsing: ts,pin,card,door,code,verify
            norm = f"{ts_str},{pin},{card},{door},{event_type},{verified}"
            norm = _normalize_rtlog_line(norm) or ""
            if norm:
                out.append(norm)
            continue

        # Header may be sent in a different request than the data rows. If the
        # device sends a 9-field transaction row without the header, normalize
        # by position.
        pos_norm = _normalize_txn_by_position(fields)
        if pos_norm:
            out.append(pos_norm)
            continue

        # Fallback: keep line as-is (tab->comma handled by _normalize_rtlog_line)
        norm = _normalize_rtlog_line(raw)
        if norm:
            # Drop common headers even when we couldn't detect mapping.
            low = norm.lower().replace(" ", "")
            if low.startswith("pin,verified,doorid"):
                continue
            out.append(norm)

    return out


def _extract_body_text(request: HttpRequest) -> str:
    # Some devices use form-encoded payloads; others send raw text.
    try:
        if request.POST and request.POST.get("data"):
            return str(request.POST.get("data") or "")
    except Exception:
        pass

    try:
        body = request.body or b""
    except Exception:
        body = b""

    try:
        return body.decode("utf-8", "replace")
    except Exception:
        try:
            return body.decode("latin-1", "replace")
        except Exception:
            return ""


def _resolve_device(*, sn: str, remote_ip: str) -> Tuple[int, str]:
    """Return (device_id, resolved_sn).

    Best-effort mapping:
      1) serial_number == sn
      2) ip_address == remote_ip
      3) fallback device_id=0 (still persist rows for later diagnosis)
    """

    try:
        from agent.models import Device

        if sn:
            dev = Device.objects.filter(serial_number=sn).first()
            if dev is not None:
                return int(dev.id), (sn or "")

        if remote_ip:
            dev = Device.objects.filter(ip_address=remote_ip).first()
            if dev is not None:
                resolved_sn = sn or getattr(dev, "serial_number", "") or ""
                return int(dev.id), resolved_sn

    except Exception:
        pass

    return 0, (sn or "")


def _broadcast_rtlog_batch(device_id: int, lines: List[str]) -> None:
    if not lines:
        return
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        layer = get_channel_layer()
        if not layer:
            return
        async_to_sync(layer.group_send)(
            "monitor",
            {
                "type": "monitor_event",
                "payload": {"type": "rtlog.batch", "device_id": device_id, "lines": lines},
            },
        )
    except Exception:
        # Push ingestion must never fail due to WS
        return


def _extract_card_candidates_from_norm(lines: List[str]) -> List[str]:
    cards: List[str] = []
    for ln in lines or []:
        try:
            parts = [p.strip() for p in str(ln or "").split(",")]
        except Exception:
            continue
        if len(parts) < 3:
            continue
        card = (parts[2] or "").strip()
        if card:
            cards.append(card)
    return cards


def _serve_pending_commands(*, device_id: int, remote_ip: str, sn: str) -> str:
    """Return newline-terminated command text for an ADMS/iClock device poll.

    We implement a simple DB-backed queue using CommandLog rows.
    Supported command shapes:
      - ADMS_RAW:<line>   -> served as-is (one line)
      - ADMS:<line>       -> served as-is (one line)
    """
    if not device_id:
        return "OK\n"

    try:
        from agent.models import CommandLog

        pending = list(
            CommandLog.objects.filter(
                device_id=int(device_id),
                status="PENDING",
            )
            .filter(command__startswith="ADMS")
            .order_by("created_at")[:25]
        )

        if not pending:
            return "OK\n"

        served_lines: List[str] = []
        served_ids: List[int] = []
        now = timezone.now()

        for row in pending:
            cmd = str(getattr(row, "command", "") or "")
            payload = ""
            if cmd.startswith("ADMS_RAW:"):
                payload = cmd[len("ADMS_RAW:") :]
            elif cmd.startswith("ADMS:"):
                payload = cmd[len("ADMS:") :]
            else:
                # allow-list ADMS prefix only
                continue

            payload = (payload or "").replace("\r\n", "\n").replace("\r", "\n").strip("\n")
            if not payload.strip():
                continue

            # Split into lines but keep order.
            for ln in payload.split("\n"):
                ln = (ln or "").strip()
                if ln:
                    served_lines.append(ln)
            served_ids.append(int(row.id))

        if not served_lines:
            return "OK\n"

        # Mark served rows.
        try:
            CommandLog.objects.filter(id__in=served_ids).update(
                status="SENT",
                executed_at=now,
                result="served via /iclock/getrequest"[:120],
            )
        except Exception:
            pass

        _audit_event(
            action="getrequest.serve",
            device_id=int(device_id),
            entity_name=f"device_id={device_id} sn={sn or ''}".strip(),
            details_obj={
                "remote_ip": remote_ip,
                "sn": sn,
                "served_count": len(served_lines),
                "commandlog_ids": served_ids,
                "preview": served_lines[:5],
            },
            remote_ip=remote_ip,
        )

        body = "\n".join(served_lines).rstrip("\n") + "\n"
        return body
    except Exception as e:
        try:
            LOG.warning("iclock_getrequest serve failed device_id=%s sn=%s ip=%s err=%s", device_id, sn, remote_ip, e)
        except Exception:
            pass
        return "OK\n"


@csrf_exempt
@require_http_methods(["GET", "POST"])
def iclock_getrequest(request: HttpRequest) -> HttpResponse:
    params = _extract_params(request)
    sn = _extract_device_sn(params)
    remote_ip = str(request.META.get("REMOTE_ADDR") or "").strip()
    device_id, resolved_sn = _resolve_device(sn=sn, remote_ip=remote_ip)

    body = _serve_pending_commands(device_id=int(device_id), remote_ip=remote_ip, sn=str(resolved_sn or sn or ""))

    # Record the poll even if no commands are served.
    try:
        _audit_event(
            action="getrequest.poll",
            device_id=int(device_id),
            entity_name=f"device_id={device_id} sn={resolved_sn or sn or ''}".strip(),
            details_obj={
                "remote_ip": remote_ip,
                "sn": sn,
                "resolved_sn": resolved_sn,
                "device_id": int(device_id),
                "response": "OK" if (body or "").strip() == "OK" else "CMD",
                "response_len": len(body or ""),
            },
            remote_ip=remote_ip,
        )
    except Exception:
        pass

    return HttpResponse(body, content_type="text/plain; charset=utf-8")


@csrf_exempt
@require_http_methods(["GET", "POST"])
def iclock_cdata(request: HttpRequest) -> HttpResponse:
    params = _extract_params(request)
    sn = _extract_device_sn(params)
    remote_ip = str(request.META.get("REMOTE_ADDR") or "").strip()
    device_id, resolved_sn = _resolve_device(sn=sn, remote_ip=remote_ip)

    body_text = _extract_body_text(request)
    body_text = (body_text or "").replace("\r\n", "\n").replace("\r", "\n")

    raw_lines = [ln for ln in body_text.split("\n") if (ln or "").strip()]
    lines = _normalize_cdata_payload(raw_lines)

    cards = _extract_card_candidates_from_norm(lines)
    table = (params.get("table") or "").strip()
    try:
        LOG.info(
            "iclock_cdata recv ip=%s sn=%s device_id=%s table=%s raw=%s norm=%s cards=%s",
            remote_ip,
            (sn or ""),
            int(device_id),
            (table or ""),
            len(raw_lines),
            len(lines),
            len(cards),
        )
    except Exception:
        pass

    # Persist all received lines so they are durable even without UI open.
    persisted = 0
    try:
        from agent.models import DeviceRealtimeLog

        if lines:
            objs = [
                DeviceRealtimeLog(device_id=int(device_id), sn=str(resolved_sn or ""), raw=str(ln))
                for ln in lines
            ]
            DeviceRealtimeLog.objects.bulk_create(objs)
            persisted = len(objs)
    except Exception as e:
        try:
            LOG.warning(
                "iclock_cdata persist failed remote_ip=%s sn=%s device_id=%s err=%s",
                remote_ip,
                sn,
                device_id,
                e,
            )
        except Exception:
            pass

    try:
        _audit_event(
            action="cdata",
            device_id=int(device_id),
            entity_name=f"device_id={device_id} sn={resolved_sn or sn or ''}".strip(),
            details_obj={
                "remote_ip": remote_ip,
                "sn": sn,
                "resolved_sn": resolved_sn,
                "device_id": int(device_id),
                "table": table,
                "raw_count": len(raw_lines),
                "normalized_count": len(lines),
                "persisted_count": int(persisted),
                "cards_present": len(cards),
                "card_preview": cards[:5],
                "line_preview": lines[:3],
            },
            remote_ip=remote_ip,
        )
    except Exception:
        pass

    # Best-effort: broadcast to monitor group so UI updates in real time.
    _broadcast_rtlog_batch(int(device_id), lines)

    return HttpResponse("OK\n", content_type="text/plain; charset=utf-8")
