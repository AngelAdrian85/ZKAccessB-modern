from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from zkeco_modern.agent.wiegand_decoder import decode_wiegand, list_known_wiegand_formats


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Decode raw Wiegand data and optionally push the decoded card into the running server.",
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--bits", help="Raw Wiegand bit string, e.g. 100000001010...")
    group.add_argument("--hex", dest="hex_value", help="Raw Wiegand value as hex, e.g. 80A12345")
    group.add_argument("--int", dest="int_value", help="Raw Wiegand value as decimal integer")
    parser.add_argument("--format", dest="format_name", help="Wiegand format name, e.g. 'Wiegand 35'")
    parser.add_argument("--bit-length", type=int, dest="bit_length", help="Expected Wiegand bit length")
    parser.add_argument("--source", default="wiegand-cli", help="Source label when pushing into the server")
    parser.add_argument("--server-url", help="Base server URL, e.g. http://127.0.0.1:8000")
    parser.add_argument("--door-id", help="Optional controller door number for push context")
    parser.add_argument("--device-id", help="Optional Django device id for push context")
    parser.add_argument("--push", action="store_true", help="POST the decoded card to /agent/api/cards/read/push/")
    parser.add_argument("--list-formats", action="store_true", help="List built-in Wiegand formats and exit")
    return parser


def _push_payload(server_url: str, payload: dict[str, object]) -> dict[str, object]:
    url = server_url.rstrip("/") + "/agent/api/cards/read/push/"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body) if body else {"ok": True}


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.list_formats:
        print(json.dumps(list_known_wiegand_formats(), indent=2, ensure_ascii=True))
        return 0

    if not any((args.bits, args.hex_value, args.int_value)):
        parser.error("one of --bits/--hex/--int is required unless --list-formats is used")

    decoded = decode_wiegand(
        bits=args.bits,
        hex_value=args.hex_value,
        int_value=args.int_value,
        format_name=args.format_name,
        bit_length=args.bit_length,
    )
    print(json.dumps(decoded, indent=2, ensure_ascii=True))

    if not args.push:
        return 0
    if not args.server_url:
        parser.error("--server-url is required with --push")

    payload = {
        "card_number": decoded.get("card_number") or "",
        "source": args.source,
        "device_id": args.device_id or "",
        "door_id": args.door_id or "",
        "wiegand_bits": decoded.get("raw_bits") or "",
        "wiegand_hex": decoded.get("raw_hex") or "",
        "wiegand_format": decoded.get("format_name") or "",
        "wiegand_bit_length": decoded.get("bit_length") or "",
    }
    try:
        resp = _push_payload(args.server_url, payload)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(body, file=sys.stderr)
        return int(exc.code or 1)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(resp, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
