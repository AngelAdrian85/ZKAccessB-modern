"""Smoke-test for the full onboarding flow (scriptic, fără UI).

Covers:
- TCP port test (prefers 14370 then 4370)
- Wizard DRAFT onboarding (matches UI flow):
    - optional clear via /agent/api/wizard/clear-device/ (blocking until OK)
    - draft door edits via /agent/crud/wizard/doors/<n>/edit/ keyed by wizard_token
    - final DB create via wizard create endpoint ONLY after prerequisites
- DB verification that Device.port == selected port
- Door provisioning defaults (enabled=True, normally_open=True) for auto-created doors

Usage (PowerShell):
    .venv/Scripts/python.exe tools/smoke_onboarding_flow.py --ip 192.168.1.235 --name "C3 test"
    .venv/Scripts/python.exe tools/smoke_onboarding_flow.py --ip 192.168.1.235 --name "C3 test" --clear-on-add
    .venv/Scripts/python.exe tools/smoke_onboarding_flow.py --ip 192.168.1.235 --name "C3 test" --cleanup

Notes:
- Runs locally against Django views using Django test client (no browser).
- Does NOT require the Django server to be running.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from typing import Any


def _filter_bad_syspath() -> None:
    bad_path_markers = ("ZKTeco", "python-support", "Python26")
    sys.path[:] = [
        p
        for p in sys.path
        if not (p and any(marker in p for marker in bad_path_markers))
    ]


def _setup_django() -> None:
    _filter_bad_syspath()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zkeco_config.settings")

    import django

    django.setup()


def _pretty(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)
    except Exception:
        return str(obj)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ip", required=True, help="Controller IP")
    ap.add_argument("--name", default=None, help="Device name to save")
    ap.add_argument("--hardware-version", default="", help="Hardware/model string")
    ap.add_argument("--serial", default="", help="Serial (optional)")
    ap.add_argument("--area-name", default="Demo", help="Zonă / Locație (required in wizard)")
    ap.add_argument(
        "--comm-password",
        default="",
        help="Controller communication password (default: empty)",
    )
    ap.add_argument("--clear-on-add", action="store_true", help="Clear device data on add")
    ap.add_argument("--cleanup", action="store_true", help="Delete created DB rows at the end")
    ap.add_argument(
        "--ports",
        default="14370,4370",
        help="Comma list of ports to test (default: 14370,4370)",
    )
    args = ap.parse_args()

    _setup_django()

    from django.contrib.auth import get_user_model
    from django.test import Client
    from django.urls import reverse

    from agent.door_provisioning import ensure_controller_doors, infer_controller_door_capacity
    from agent.models import Device, Door

    ip = str(args.ip).strip()
    name = (args.name or f"Centrală {ip}").strip()
    serial = str(args.serial or "").strip()
    hardware_version = str(args.hardware_version or "").strip()
    area_name = str(args.area_name or "").strip() or "Demo"
    comm_password = str(args.comm_password or "").strip()
    ports = [int(p.strip()) for p in str(args.ports).split(",") if p.strip().isdigit()]
    if not ports:
        ports = [14370, 4370]

    if not serial:
        serial = f"SMOKE-{ip}-{int(time.time())}"

    wizard_token = f"smoke_{ip.replace('.', '_')}_{int(time.time())}"

    c = Client(enforce_csrf_checks=False)

    User = get_user_model()
    smoke_user, _created = User.objects.get_or_create(
        username="smoke_onboarding",
        defaults={"is_staff": True, "is_superuser": True, "email": "smoke@local"},
    )
    try:
        if not getattr(smoke_user, "is_staff", False) or not getattr(smoke_user, "is_superuser", False):
            smoke_user.is_staff = True
            smoke_user.is_superuser = True
            smoke_user.save(update_fields=["is_staff", "is_superuser"])
    except Exception:
        pass
    c.force_login(smoke_user)

    # 1) TCP port test
    port_test_url = reverse("device-port-test")
    resp = c.get(
        port_test_url,
        {
            "ip": ip,
            "ports": ",".join(str(p) for p in ports),
            "quick": 1,
            "probe": 1,
            "comm_password": comm_password,
        },
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
    )
    try:
        port_test = resp.json()
    except Exception:
        print("[FAIL] device-port-test did not return JSON")
        print(resp.status_code)
        print(resp.content[:4000])
        return 2

    print("\n== Port test response ==")
    print(_pretty(port_test))

    if not (port_test and port_test.get("ok")):
        print("[FAIL] port test endpoint returned ok=false")
        return 3

    # With probe enabled, only accept a protocol-responding port.
    best_responding_port = port_test.get("best_responding_port", None)
    best_open_port = port_test.get("best_open_port", None)

    if best_responding_port is None:
        if bool(port_test.get("open")):
            print(
                f"[FAIL] Found TCP-open port(s) {port_test.get('open_ports')}, but none respond to controller protocol. "
                f"(best_open_port={best_open_port})"
            )
            return 4
        best_port = int(best_open_port or 0) or (ports[0] if ports else 4370)
        print(f"[WARN] No tested ports are open for {ip}. Continuing with best_port={best_port}.")
    else:
        best_port = int(best_responding_port)

    def _post_wizard_create(include_clear_on_add_flag: bool) -> tuple[int | None, str, int, int | None]:
        create_url_local = reverse("crud-device-create-access")
        post_local: dict[str, Any] = {
            "wizard_token": wizard_token,
            "name": name,
            "serial_number": serial,
            "device_type": "access_panel",
            "comm_mode": "tcp",
            "ip_address": ip,
            "port": str(int(best_port)),
            "comm_password": comm_password,
            "rs485_port": "COM1",
            "rs485_baudrate": "9600",
            "rs485_address": "",
            "area_name": area_name,
            "hardware_version": hardware_version,
            "enabled": "on",
            "auto_sync_time": "on",
        }
        if include_clear_on_add_flag:
            post_local["clear_on_add"] = "on"

        r = c.post(
            create_url_local + f"?wizard=1&wizard_token={wizard_token}",
            data=post_local,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        try:
            html_local = r.content.decode("utf-8", errors="replace")
        except Exception:
            html_local = str(r.content)

        created_local: int | None = None
        m = re.search(r'data-access-saved="1"[^>]*data-device-id="(\d+)"', html_local)
        if m:
            try:
                created_local = int(m.group(1))
            except Exception:
                created_local = None

        clear_cmd_local: int | None = None
        m2 = re.search(r'data-clear-command-id="(\d+)"', html_local)
        if m2:
            try:
                clear_cmd_local = int(m2.group(1))
            except Exception:
                clear_cmd_local = None

        return created_local, html_local, int(r.status_code), clear_cmd_local

    created_id, html, status_code, clear_cmd_id = _post_wizard_create(
        include_clear_on_add_flag=bool(args.clear_on_add)
    )

    if created_id is None:
        print("\n== Wizard create (initial) did not complete ==")
        print(f"status={status_code} bytes={len(html.encode('utf-8', errors='ignore'))}")
        print("Falling back to draft wizard flow...")

        if args.clear_on_add:
            clear_url = reverse("wizard-clear-device")
            resp0 = c.post(
                clear_url,
                data=json.dumps({
                    "ip": ip,
                    "port": int(best_port),
                    "comm_password": comm_password,
                    "wizard_token": wizard_token,
                }),
                content_type="application/json",
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
            try:
                clear_start = resp0.json()
            except Exception:
                print("[FAIL] wizard-clear-device did not return JSON")
                print(resp0.status_code)
                print(resp0.content[:4000])
                return 20

            print("\n== Wizard clear start ==")
            print(_pretty(clear_start))

            if not (clear_start and clear_start.get("ok") and int(clear_start.get("command_id") or 0) > 0):
                print("[FAIL] wizard clear start failed")
                return 21

            cmd_id = int(clear_start.get("command_id") or 0)
            status_url = reverse("command-status", args=[cmd_id])
            deadline = time.time() + 900
            last = None
            while time.time() < deadline:
                rr = c.get(status_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
                try:
                    st = rr.json()
                except Exception:
                    st = None
                if st and st.get("ok"):
                    # Print incremental progress when it changes.
                    if not last or (st.get('status') != last.get('status') or st.get('result') != last.get('result')):
                        print(f"[clear] status={st.get('status')} result={st.get('result')}")
                    last = st
                    status = str(st.get("status") or "").upper()
                    if status == "OK":
                        print("\n== Wizard clear OK ==")
                        print(_pretty(st))
                        break
                    if status in ("ERR", "ERROR", "FAILED"):
                        print("\n== Wizard clear ERR ==")
                        print(_pretty(st))
                        return 22
                time.sleep(1.0)
            else:
                print("[FAIL] wizard clear timed out")
                print(_pretty(last))
                return 23

        tmp = Device(
            device_type="access_panel",
            comm_mode="tcp",
            ip_address=ip,
            port=int(best_port),
            hardware_version=hardware_version,
        )
        cap = int(infer_controller_door_capacity(tmp) or 0)
        if cap <= 0:
            cap = 1
        print("\n== Inferred door capacity ==")
        print({"hardware_version": hardware_version, "capacity": cap})

        for dn in range(1, cap + 1):
            door_url = reverse("wizard-door-draft-edit", args=[dn])
            door_post = {
                "wizard_token": wizard_token,
                "door_number": str(dn),
                "name": f"Ușă {dn}",
                "reader_in_custom_name": f"{ip}-{dn} In",
                "reader_out_custom_name": f"{ip}-{dn} Out",
                "normally_open": "on",
                "enabled": "on",
            }
            r = c.post(
                door_url + f"?wizard=1&wizard_token={wizard_token}&modal=1",
                data=door_post,
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
            html_d = r.content.decode("utf-8", errors="replace")
            if "data-wizard-door-saved=\"1\"" not in html_d:
                print(f"[FAIL] draft door save failed for door {dn}")
                print(r.status_code)
                print(html_d[:4000])
                return 30

        created_id, html, status_code, clear_cmd_id = _post_wizard_create(
            include_clear_on_add_flag=False
        )

    print("\n== Wizard create HTTP ==")
    print(f"status={status_code} bytes={len(html.encode('utf-8', errors='ignore'))}")

    if created_id is None:
        print("[FAIL] Wizard create did not return saved-inner HTML (likely validation error)")
        try:
            from agent.forms import DeviceExtendedForm

            f = DeviceExtendedForm({
                "wizard_token": wizard_token,
                "name": name,
                "serial_number": serial,
                "device_type": "access_panel",
                "comm_mode": "tcp",
                "ip_address": ip,
                "port": str(int(best_port)),
                "comm_password": "",
                "rs485_port": "COM1",
                "rs485_baudrate": "9600",
                "rs485_address": "",
                "area_name": area_name,
                "hardware_version": hardware_version,
                "enabled": "on",
                "auto_sync_time": "on",
            }, wizard=True)
            ok_local = f.is_valid()
            print("\n== Local form validation ==")
            print(f"is_valid={ok_local}")
            try:
                print(_pretty({k: [str(x) for x in v] for k, v in f.errors.items()}))
            except Exception:
                print(str(f.errors))
        except Exception as _e:
            print(f"[WARN] Could not run local form validation: {_e}")

        try:
            errs = re.findall(
                r'(?:<div class="form-errors"[^>]*>|<span class="form-errors"[^>]*>)(.*?)(?:</div>|</span>)',
                html,
                flags=re.IGNORECASE | re.DOTALL,
            )
            if errs:
                print("\n== Extracted form-errors ==")
                for i, raw in enumerate(errs[:12], start=1):
                    msg = re.sub(r'<[^>]+>', '', raw)
                    msg = re.sub(r'\s+', ' ', msg).strip()
                    if msg:
                        print(f"- {i}. {msg}")
        except Exception:
            pass
        print("\n== HTML (head) ==")
        print(html[:4000])
        return 4

    print("\n== Wizard create result ==")
    print({"id": created_id, "wizard_token": wizard_token, "clear_command_id": clear_cmd_id})

    dev = Device.objects.filter(pk=created_id).first()
    if not dev:
        print("[FAIL] Device not found in DB after wizard create")
        return 6

    print("\n== DB device ==")
    print(f"id={dev.id} name={dev.name} ip={dev.ip_address} port={dev.port}")

    if int(dev.port or 0) != int(best_port):
        print(f"[FAIL] Device.port mismatch: expected {best_port}, got {dev.port}")
        return 7

    prov = ensure_controller_doors(dev)
    print("\n== Door provisioning ==")
    print(f"capacity={prov.capacity} created={prov.created} existing={prov.existing}")

    d1 = Door.objects.filter(device=dev).order_by("door_number", "id").first()
    if not d1:
        print("[FAIL] No doors linked to device after provisioning")
        return 8

    print("\n== Sample door ==")
    print(
        f"door_id={d1.id} door_no={d1.door_number} enabled={d1.enabled} normally_open={getattr(d1,'normally_open',None)}"
    )

    if not bool(d1.enabled):
        print("[FAIL] Door.enabled is not True")
        return 9

    if not bool(getattr(d1, "normally_open", False)):
        print("[FAIL] Door.normally_open is not True")
        return 10

    if args.cleanup:
        try:
            Door.objects.filter(device_id=created_id).delete()
        except Exception:
            pass
        try:
            Device.objects.filter(pk=created_id).delete()
        except Exception:
            pass
        print("\n== Cleanup ==")
        print({"deleted_device_id": created_id})

    print("\n[PASS] Onboarding smoke-test complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
