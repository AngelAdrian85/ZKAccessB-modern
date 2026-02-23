"""Minimal HTTP listener to observe ZKTeco 'push' / ADMS callbacks.

This started as a generic logger; it's now ADMS-aware enough to help you capture
real controller traffic and iterate quickly:
    - logs remote IP + parsed query params
    - dumps request bodies to disk (so you can inspect them later)
    - responds to `/iclock/getrequest` with queued commands from a text file

Run:
    .\.venv\Scripts\python.exe scripts\push_listener.py --host 0.0.0.0 --port 8088

Optional:
    --dump-dir push_dumps
    --command-file adms_commands.txt
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


_DUMP_DIR = Path("push_dumps")
_COMMAND_FILE = Path("adms_commands.txt")


class Handler(BaseHTTPRequestHandler):
    server_version = "ZKADMSProbe/0.2"

    def log_message(self, fmt: str, *args) -> None:
        # silence default logging; we print our own summary
        return

    def _read_body(self) -> bytes:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except Exception:
            length = 0
        if length <= 0:
            return b""
        return self.rfile.read(length)

    def _now_tag(self) -> str:
        return _dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    def _remote(self) -> str:
        try:
            return f"{self.client_address[0]}:{self.client_address[1]}"
        except Exception:
            return "?:?"

    def _parsed_url(self):
        return urlsplit(self.path)

    def _dump_to_disk(self, *, body: bytes) -> None:
        try:
            _DUMP_DIR.mkdir(parents=True, exist_ok=True)
            parsed = self._parsed_url()
            safe_path = parsed.path.strip("/").replace("/", "__") or "root"
            fn = f"{self._now_tag()}__{self.command}__{safe_path}.txt"
            p = _DUMP_DIR / fn
            header_lines = [
                f"REMOTE: {self._remote()}",
                f"{self.command} {self.path}",
            ]
            for k, v in self.headers.items():
                header_lines.append(f"{k}: {v}")
            header_blob = ("\n".join(header_lines) + "\n\n").encode("utf-8", "replace")
            with p.open("wb") as f:
                f.write(header_blob)
                f.write(body or b"")
        except Exception as e:
            print(f"[WARN] dump failed: {type(e).__name__}: {e}")

    def _dump(self, body: bytes) -> None:
        parsed = self._parsed_url()
        q = parse_qs(parsed.query or "", keep_blank_values=True)
        print("\n==== REQUEST ====")
        print(f"REMOTE: {self._remote()}")
        print(f"{self.command} {self.path}")
        if q:
            print("\n-- query --")
            for k in sorted(q.keys()):
                vals = q.get(k) or []
                if len(vals) == 1:
                    print(f"{k}={vals[0]}")
                else:
                    print(f"{k}={vals}")
        for k, v in self.headers.items():
            print(f"{k}: {v}")
        if body:
            try:
                text = body.decode("utf-8", "replace")
                print("\n-- body (utf-8) --")
                print(text)
            except Exception:
                print("\n-- body (bytes) --")
                print(body)
        else:
            print("\n-- body: <empty> --")

        self._dump_to_disk(body=body)

    def _reply_ok(self, body: bytes = b"OK\n") -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _reply_text(self, body: str) -> None:
        data = (body or "").encode("utf-8", "replace")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _handle_getrequest(self) -> None:
        # Many ZKTeco devices poll this endpoint to receive server commands.
        # We implement a simple file-backed queue:
        # - if command file is non-empty, return its contents and truncate it
        # - otherwise return OK
        try:
            p = _COMMAND_FILE
            if not p.exists():
                self._reply_ok(b"OK\n")
                return
            cmd = p.read_text(encoding="utf-8", errors="replace")
            cmd = cmd.replace("\r\n", "\n")
            if not cmd.strip():
                self._reply_ok(b"OK\n")
                return

            # Truncate after serving once.
            try:
                p.write_text("", encoding="utf-8")
            except Exception:
                pass

            if not cmd.endswith("\n"):
                cmd += "\n"
            self._reply_text(cmd)
        except Exception as e:
            print(f"[WARN] getrequest reply failed: {type(e).__name__}: {e}")
            self._reply_ok(b"OK\n")

    def do_GET(self) -> None:  # noqa: N802
        body = self._read_body()
        self._dump(body)
        parsed = self._parsed_url()
        if parsed.path.rstrip("/") == "/iclock/getrequest":
            self._handle_getrequest()
            return
        self._reply_ok(b"OK\n")

    def do_POST(self) -> None:  # noqa: N802
        body = self._read_body()
        self._dump(body)
        self._reply_ok(b"OK\n")


def main() -> int:
    global _DUMP_DIR, _COMMAND_FILE

    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8088)
    ap.add_argument("--dump-dir", default=str(_DUMP_DIR))
    ap.add_argument("--command-file", default=str(_COMMAND_FILE))
    ns = ap.parse_args()

    _DUMP_DIR = Path(ns.dump_dir)
    _COMMAND_FILE = Path(ns.command_file)

    # Avoid failing on missing CWD perms; dump dir will be created lazily.
    try:
        os.makedirs(str(_DUMP_DIR), exist_ok=True)
    except Exception:
        pass

    httpd = HTTPServer((ns.host, ns.port), Handler)
    print(f"Listening on http://{ns.host}:{ns.port} (Ctrl+C to stop)")
    print(f"Dump dir: {_DUMP_DIR}")
    print(f"Command file: {_COMMAND_FILE}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
