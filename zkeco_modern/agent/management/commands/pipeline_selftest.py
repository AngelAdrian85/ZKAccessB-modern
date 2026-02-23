from __future__ import annotations

import datetime as _dt

from django.core.management.base import BaseCommand
from django.test.client import RequestFactory


class Command(BaseCommand):
    help = (
        "End-to-end self-test for the ADMS/iClock push pipeline: "
        "(1) inject synthetic cdata, (2) enqueue a getrequest command, "
        "(3) simulate device poll and verify it is served + audited."
    )

    def add_arguments(self, parser):
        parser.add_argument("--device-id", type=int, default=0, help="Device.id to target")
        parser.add_argument("--sn", type=str, default="", help="Device serial number (SN)")
        parser.add_argument(
            "--remote-ip",
            type=str,
            default="",
            help="REMOTE_ADDR to simulate (defaults to device.ip_address)",
        )

        parser.add_argument(
            "--inject-card",
            type=str,
            default="",
            help="If set, POST a synthetic RTLOG line with this card number to /iclock/cdata",
        )
        parser.add_argument(
            "--inject-door",
            type=int,
            default=1,
            help="Door value for injected RTLOG (default 1)",
        )

        parser.add_argument(
            "--enqueue-adms-raw",
            type=str,
            default="",
            help="If set, enqueue a CommandLog row 'ADMS_RAW:<value>' for this device",
        )

        parser.add_argument(
            "--enqueue-door-open",
            action="store_true",
            help="If set, call the Django door_open API (queues DOOR_OPEN via CommandLog)",
        )
        parser.add_argument(
            "--door",
            type=str,
            default="1",
            help="Door pk or door_number passed to door_open (default '1')",
        )
        parser.add_argument(
            "--simulate-getrequest",
            action="store_true",
            help="If set, call the /iclock/getrequest view and print the response body",
        )

        parser.add_argument(
            "--show-audit",
            action="store_true",
            help="If set, print the last few AuditLog rows for module=iclock",
        )

    def handle(self, *args, **options):
        from agent.models import AuditLog, CommandLog, Device, DeviceRealtimeLog
        from agent.iclock_views import iclock_cdata, iclock_getrequest
        from agent.views import door_open

        from django.contrib.auth import get_user_model

        device_id = int(options.get("device_id") or 0)
        sn = str(options.get("sn") or "").strip()

        dev = None
        if device_id:
            dev = Device.objects.filter(id=device_id).first()
        if dev is None and sn:
            dev = Device.objects.filter(serial_number=sn).first()
        if dev is None:
            raise SystemExit("Device not found. Use --device-id or --sn.")

        device_id = int(dev.id)
        sn = dev.serial_number or sn

        remote_ip = str(options.get("remote_ip") or "").strip() or (dev.ip_address or "")
        self.stdout.write(f"Target device: id={device_id} sn={sn} ip={dev.ip_address} port={dev.port} enabled={dev.enabled}")
        if remote_ip:
            self.stdout.write(f"Simulated REMOTE_ADDR: {remote_ip}")

        rf = RequestFactory()

        injected = str(options.get("inject_card") or "").strip()
        if injected:
            now = _dt.datetime.now().replace(microsecond=0)
            ts = now.strftime("%Y-%m-%d %H:%M:%S")
            door = int(options.get("inject_door") or 1)
            body = f"{ts},0,{injected},{door},0,0\n"

            req = rf.post(
                f"/iclock/cdata/?SN={sn}&table=rtlog",
                data=body,
                content_type="text/plain",
                REMOTE_ADDR=remote_ip,
            )
            resp = iclock_cdata(req)
            self.stdout.write(f"Injected cdata: status={getattr(resp, 'status_code', '?')} bytes={len(getattr(resp, 'content', b'') or b'')}")

            last = DeviceRealtimeLog.objects.order_by("-id").first()
            if not last:
                raise SystemExit("Injection failed: DeviceRealtimeLog is empty")
            self.stdout.write(f"Last DeviceRealtimeLog: id={last.id} device_id={last.device_id} raw={last.raw!r}")

        raw_cmd = str(options.get("enqueue_adms_raw") or "").strip()
        if raw_cmd:
            row = CommandLog.objects.create(device=dev, command=f"ADMS_RAW:{raw_cmd}", status="PENDING")
            self.stdout.write(f"Enqueued CommandLog: id={row.id} command={row.command!r} status={row.status}")

        if bool(options.get("enqueue_door_open")):
            door_arg = str(options.get("door") or "1").strip() or "1"
            User = get_user_model()
            user, _ = User.objects.get_or_create(
                username="selftest",
                defaults={"is_staff": True, "is_superuser": True},
            )
            if not user.is_staff:
                user.is_staff = True
                user.is_superuser = True
                user.save(update_fields=["is_staff", "is_superuser"])

            req = rf.post(
                f"/agent/api/devices/{device_id}/doors/{door_arg}/open/",
                data={},
                REMOTE_ADDR=remote_ip,
            )
            req.user = user
            resp = door_open(req, int(device_id), str(door_arg))
            self.stdout.write(
                f"door_open enqueue: status={getattr(resp, 'status_code', '?')} body={(getattr(resp, 'content', b'') or b'').decode('utf-8','replace')[:200]}"
            )
            last_cmd = CommandLog.objects.filter(device=dev).order_by("-id").first()
            if last_cmd is not None:
                self.stdout.write(f"Latest CommandLog: id={last_cmd.id} status={last_cmd.status} command={last_cmd.command!r}")

        if bool(options.get("simulate_getrequest")):
            req = rf.get(f"/iclock/getrequest/?SN={sn}", REMOTE_ADDR=remote_ip)
            resp = iclock_getrequest(req)
            body = (getattr(resp, "content", b"") or b"").decode("utf-8", "replace")
            self.stdout.write("/iclock/getrequest response:")
            self.stdout.write(body.rstrip("\n"))

            # show last served command row
            served = CommandLog.objects.filter(device=dev).order_by("-id").first()
            if served is not None:
                self.stdout.write(f"Latest CommandLog now: id={served.id} status={served.status} result={served.result!r}")

        if bool(options.get("show_audit")):
            qs = AuditLog.objects.filter(module="iclock", entity_id=device_id).order_by("-timestamp")[:10]
            self.stdout.write("\nRecent AuditLog (module=iclock):")
            for a in qs:
                self.stdout.write(
                    f"- {a.timestamp:%Y-%m-%d %H:%M:%S} action={a.action} ip={a.ip_address} details_len={len(a.details or '')}"
                )

        # Always show current inbound signal summary.
        recent = list(DeviceRealtimeLog.objects.filter(device_id=device_id).order_by("-id")[:5])
        self.stdout.write("\nRecent DeviceRealtimeLog rows:")
        for r in reversed(recent):
            self.stdout.write(f"- id={r.id} created_at={getattr(r, 'created_at', None)} raw={str(r.raw or '')[:180]}")
