import signal
import sys
import logging
from typing import List

from django.core.management.base import BaseCommand

from agent.modern_comm_center import build_and_run_stub

LOG = logging.getLogger("modern_comm_center.command")


class Command(BaseCommand):
    help = "Run the modern communication center agent (device polling, rtlog, new log downloads)."

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=float, default=1.0, help="Polling interval in seconds (default 1.0)")
        parser.add_argument("--hours", type=str, default="", help="Comma-separated hours for new log download (e.g. 0,6,12,18)")
        parser.add_argument("--redis", action="store_true", help="Enable Redis-backed queues/heartbeat (REDIS_URL env or --redis-url)")
        parser.add_argument("--redis-url", type=str, default=None, help="Redis connection URL (overrides REDIS_URL env)")
        parser.add_argument("--json-logs", action="store_true", help="Emit JSON structured logs to stdout")
        parser.add_argument("--metrics", action="store_true", help="Print metrics counters periodically")
        parser.add_argument("--once", action="store_true", help="Run a single polling cycle and exit")
        parser.add_argument("--driver", type=str, choices=["auto", "stub", "socket", "sdk"], default="auto", help="Select driver backend")
        parser.add_argument("--discover-subnet", type=str, default=None, help="Optional CIDR subnet scan for controllers (e.g. 192.168.1.0/24)")
        parser.add_argument("--ports", type=str, default=None, help="Comma-separated ports for discovery override (default 4370,80)")

    def handle(self, *args, **options):
        interval: float = options["interval"]
        hours_raw: str = options["hours"]
        use_redis: bool = options["redis"]
        redis_url: str | None = options["redis_url"]
        download_hours: List[int] = []
        if hours_raw:
            try:
                download_hours = [int(h) for h in hours_raw.split(',') if h.strip()]
            except ValueError:
                self.stderr.write("Invalid hours list; expected integers")
                return

        self.stdout.write(f"Starting CommCenter (interval={interval}, hours={download_hours}, redis={use_redis})")

        if options["json_logs"]:
            try:
                import json, logging
                class JsonFormatter(logging.Formatter):
                    def format(self, record):  # pragma: no cover
                        base = {
                            "level": record.levelname,
                            "name": record.name,
                            "msg": record.getMessage(),
                            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
                        }
                        if record.exc_info:
                            base["exception"] = self.formatException(record.exc_info)
                        return json.dumps(base)
                root = logging.getLogger()
                for h in root.handlers:
                    h.setFormatter(JsonFormatter())
            except Exception:
                self.stderr.write("Failed enabling JSON logs; continuing with default format")

        center = build_and_run_stub(poll_interval=interval,
                                    use_redis=use_redis,
                                    redis_url=redis_url,
                        download_hours=download_hours,
                        driver=options["driver"]) 
        import agent.modern_comm_center as mcc
        mcc.ACTIVE_CENTER = center  # expose global reference for API actions

        if options.get("discover_subnet"):
            from agent.server_discovery import discover_devices
            subnet = options["discover_subnet"]
            ports_opt = options.get("ports")
            ports_list = None
            if ports_opt:
                try:
                    ports_list = [int(p) for p in ports_opt.split(',') if p.strip()]
                except ValueError:
                    self.stderr.write("Invalid --ports list; expected integers")
                    ports_list = None
            self.stdout.write(f"Scanning subnet {subnet}...")
            found = discover_devices(subnet, ports=ports_list)
            if found:
                self.stdout.write(f"Discovered {len(found)} candidate hosts: {found}")
            else:
                self.stdout.write("Discovered 0 candidate hosts (verify subnet, local interface, firewall, and port list)")

        if options["once"]:
            # Single-cycle mode for quick validation
            center.run_once()
            if options["metrics"]:
                last_cycle = None
                try:
                    last_cycle = center.heartbeat_backend.get("last_cycle")  # type: ignore[attr-defined]
                except Exception:
                    pass
                self.stdout.write(
                    f"metrics rtlog_lines={center.total_rtlog_lines} event_logs={center.total_event_logs} last_cycle={last_cycle}"
                )
            center.stop()
            return

        # Graceful shutdown handling
        def _handle_signal(signum, frame):  # noqa: D401
            self.stdout.write(f"Received signal {signum}; stopping CommCenter...")
            center.stop()
            sys.exit(0)

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, _handle_signal)
            except Exception:  # pragma: no cover
                pass

        # Block main thread while background thread runs
        try:
            while True:
                # Heartbeat fetch (works for both memory and Redis backends)
                if options["metrics"]:
                    last_cycle = None
                    try:
                        last_cycle = center.heartbeat_backend.get("last_cycle")  # type: ignore[attr-defined]
                    except Exception:
                        pass
                    self.stdout.write(
                        f"metrics rtlog_lines={center.total_rtlog_lines} event_logs={center.total_event_logs} last_cycle={last_cycle}",
                        ending='\r'
                    )
                # Use a small sleep to avoid busy loop
                import time
                time.sleep(max(0.5, interval))
        except KeyboardInterrupt:
            self.stdout.write("KeyboardInterrupt received; stopping...")
            center.stop()
            return