from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from typing import Any


HEARTBEAT_PATH = os.path.join(os.path.expanduser("~"), "zkeco_reader_heartbeat_wiegand.json")
TRACE_PATH = os.environ.get(
    "ZKACCESS_WIEGAND_TRACE_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tmp_wiegand_listener_trace.jsonl"),
)


def load_listener_defaults() -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "listen_host": "0.0.0.0",
        "listen_port": 9002,
        "device_id": "",
        "door_id": "",
        "door_pk": "",
        "format_name": "",
        "format_id": "",
        "source": "w26-hardware-tap",
    }
    try:
        cfg_path = os.path.join(os.path.dirname(__file__), "card_readers.json")
        if not os.path.exists(cfg_path):
            return defaults
        with open(cfg_path, "r", encoding="utf-8-sig") as handle:
            cfg = json.load(handle) or {}
        wiegand = cfg.get("wiegand") or {}
        acp = cfg.get("acp") or {}
        if wiegand.get("listen_host") not in (None, ""):
            defaults["listen_host"] = str(wiegand.get("listen_host") or "").strip() or defaults["listen_host"]
        if wiegand.get("port") not in (None, ""):
            defaults["listen_port"] = int(str(wiegand.get("port") or "9002").strip() or "9002")
        elif acp.get("port") not in (None, ""):
            defaults["listen_port"] = int(str(acp.get("port") or "9001").strip() or "9001")
        for key in ("device_id", "door_id", "door_pk", "format_name", "format_id", "source"):
            if wiegand.get(key) not in (None, ""):
                defaults[key] = str(wiegand.get(key) or "").strip()
        for key in ("device_id", "door_id", "door_pk"):
            if defaults.get(key):
                continue
            if acp.get(key) not in (None, ""):
                defaults[key] = str(acp.get(key) or "").strip()
    except Exception:
        return defaults
    return defaults


LISTENER_DEFAULTS = load_listener_defaults()


def trace(event: str, **fields: Any) -> None:
    try:
        record = {"ts": time.time(), "event": event, "pid": os.getpid()}
        record.update(fields)
        with open(TRACE_PATH, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
    except Exception:
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Listen for raw Wiegand payloads and forward them to /agent/api/cards/read/push/.",
    )
    parser.add_argument("--server-url", default="", help="Base server URL, e.g. http://127.0.0.1:15437. If omitted, detect from zkeco_tray_config.ini.")
    parser.add_argument("--listen-host", default=str(LISTENER_DEFAULTS.get("listen_host") or "0.0.0.0"), help="Host/IP to bind the TCP listener")
    parser.add_argument("--listen-port", type=int, default=int(LISTENER_DEFAULTS.get("listen_port") or 9001), help="TCP port to bind the listener")
    parser.add_argument("--format-name", default=str(LISTENER_DEFAULTS.get("format_name") or ""), help="Default Wiegand format name to attach")
    parser.add_argument("--format-id", default=str(LISTENER_DEFAULTS.get("format_id") or ""), help="Default Wiegand format id to attach")
    parser.add_argument("--device-id", default=str(LISTENER_DEFAULTS.get("device_id") or ""), help="Optional Django device id for context")
    parser.add_argument("--door-id", default=str(LISTENER_DEFAULTS.get("door_id") or ""), help="Optional controller door number for context")
    parser.add_argument("--door-pk", default=str(LISTENER_DEFAULTS.get("door_pk") or ""), help="Optional Django door primary key")
    parser.add_argument("--source", default=str(LISTENER_DEFAULTS.get("source") or "wiegand-listener"), help="Source label stored in monitor stream")
    return parser


def detect_server_url(explicit_url: str = "") -> str:
    value = str(explicit_url or "").strip()
    if value:
        return value.rstrip("/")
    port = 15437
    try:
        ini_path = os.path.join(os.path.expanduser("~"), "zkeco_tray_config.ini")
        if os.path.exists(ini_path):
            import configparser

            cp = configparser.ConfigParser(strict=False)
            cp.read(ini_path, encoding="utf-8-sig")
            if cp.has_section("tray") and cp.has_option("tray", "port"):
                port = int(cp.get("tray", "port"))
    except Exception:
        port = 15437
    return f"http://127.0.0.1:{port}"


def post_payload(server_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    trace("push_attempt", server_url=server_url, payload=payload)
    req = urllib.request.Request(
        server_url.rstrip("/") + "/agent/api/cards/read/push/",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        trace("push_ok", status=getattr(resp, "status", None), body=(body or "")[:200])
    return json.loads(body) if body else {"ok": True}


def touch_heartbeat(args: argparse.Namespace, *, source: str = "idle") -> None:
    try:
        hb = {
            "ts": time.time(),
            "source": source,
            "listen_host": str(getattr(args, "listen_host", "") or ""),
            "listen_port": int(getattr(args, "listen_port", 0) or 0),
            "server_url": str(getattr(args, "server_url", "") or ""),
        }
        with open(HEARTBEAT_PATH, "w", encoding="utf-8") as handle:
            json.dump(hb, handle)
    except Exception:
        pass


def _sanitize_frame_text(text: str) -> str:
    frame = str(text or "").replace("\x00", "").strip()
    return frame.strip("\r")


def _sanitize_frame_bytes(raw: bytes) -> bytes:
    return (raw or b"").strip().strip(b"\r").strip(b"\x00")


def parse_frame(text: str) -> dict[str, Any] | None:
    frame = _sanitize_frame_text(text)
    if not frame:
        return None
    upper = frame.upper()
    if upper.startswith("BITS:"):
        return {"wiegand_bits": frame.split(":", 1)[1].strip()}
    if upper.startswith("HEX:"):
        return {"wiegand_hex": frame.split(":", 1)[1].strip()}
    if upper.startswith("INT:"):
        return {"wiegand_int": frame.split(":", 1)[1].strip()}
    if upper.startswith("CARD:"):
        return {"card_number": frame.split(":", 1)[1].strip()}
    try:
        obj = json.loads(frame)
    except Exception:
        obj = None
    if isinstance(obj, dict):
        if obj.get("card") and not obj.get("card_number"):
            obj["card_number"] = obj.get("card")
        return obj
    if set(frame) <= {"0", "1"} and len(frame) >= 8:
        return {"wiegand_bits": frame}
    return {"card_number": frame}


def merge_defaults(payload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    merged = {
        "source": args.source,
        **payload,
    }
    if args.device_id and not merged.get("device_id"):
        merged["device_id"] = args.device_id
    if args.door_id and not merged.get("door_id"):
        merged["door_id"] = args.door_id
    if args.door_pk and not merged.get("door_pk"):
        merged["door_pk"] = args.door_pk
    if args.format_id and not merged.get("wiegand_format_id"):
        merged["wiegand_format_id"] = args.format_id
    if args.format_name and not merged.get("wiegand_format"):
        merged["wiegand_format"] = args.format_name
    return merged


def handle_frame(text: str, args: argparse.Namespace) -> None:
    payload = parse_frame(text)
    if not payload:
        trace("frame_ignored", preview=_sanitize_frame_text(text)[:200])
        return
    payload = merge_defaults(payload, args)
    trace("frame_parsed", payload=payload)
    print("[WIEGAND] RX", json.dumps(payload, ensure_ascii=True), flush=True)
    try:
        response = post_payload(args.server_url, payload)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        trace("push_http_error", status=exc.code, body=(body or "")[:200], payload=payload)
        print(f"[WIEGAND] HTTP {exc.code}: {body}", file=sys.stderr, flush=True)
        return
    except Exception as exc:
        trace("push_error", error=str(exc), payload=payload)
        print(f"[WIEGAND] PUSH ERROR: {exc}", file=sys.stderr, flush=True)
        return
    touch_heartbeat(args, source="frame")
    trace("frame_processed", response=response)
    print("[WIEGAND] OK", json.dumps(response, ensure_ascii=True), flush=True)


def handle_client(conn: socket.socket, addr: tuple[str, int], args: argparse.Namespace) -> None:
    conn.settimeout(5)
    buf = b""
    trace("client_connected", host=str(addr[0]), port=int(addr[1]))
    try:
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            trace("client_chunk", host=str(addr[0]), port=int(addr[1]), size=len(chunk), preview=chunk[:128].decode("utf-8", errors="replace"))
            buf += chunk
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                text = _sanitize_frame_bytes(raw).decode("utf-8", errors="ignore")
                if text:
                    handle_frame(text, args)
    except Exception as exc:
        trace("client_error", host=str(addr[0]), port=int(addr[1]), error=str(exc))
        print(f"[WIEGAND] CLIENT ERROR: {exc}", file=sys.stderr, flush=True)
    finally:
        tail = _sanitize_frame_bytes(buf).decode("utf-8", errors="ignore")
        if tail:
            trace("client_tail", host=str(addr[0]), port=int(addr[1]), preview=tail[:128])
            handle_frame(tail, args)
        try:
            conn.close()
        except Exception:
            pass
        trace("client_closed", host=str(addr[0]), port=int(addr[1]))


def serve(args: argparse.Namespace) -> int:
    args.server_url = detect_server_url(getattr(args, "server_url", ""))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    except Exception:
        pass
    sock.bind((args.listen_host, int(args.listen_port)))
    sock.listen(10)
    touch_heartbeat(args, source="listening")
    trace(
        "listener_bound",
        host=args.listen_host,
        port=int(args.listen_port),
        server_url=args.server_url,
        source=args.source,
    )
    print(
        f"[WIEGAND] Listening on {args.listen_host}:{args.listen_port} -> {args.server_url.rstrip('/')}/agent/api/cards/read/push/",
        flush=True,
    )
    while True:
        conn, addr = sock.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr, args), daemon=True)
        t.start()


if __name__ == "__main__":
    raise SystemExit(serve(build_parser().parse_args()))
