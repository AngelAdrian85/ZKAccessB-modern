from __future__ import annotations

import re
from typing import Any


_HEADER_ALIASES = {
    "uid": "uid",
    "pin": "pin",
    "cardno": "cardno",
    "card": "cardno",
    "transactioncardno": "cardno",
    "vicecard": "vicecard",
    "group": "group",
    "password": "password",
    "starttime": "start_time",
    "endtime": "end_time",
    "name": "name",
    "superauthorize": "super_authorize",
    "disable": "disable",
    "verified": "verified",
    "doorid": "door_id",
    "eventtype": "event_type",
    "inoutstate": "in_out_state",
    "timesecond": "time_second",
    "index": "index",
    "sitecode": "sitecode",
    "time": "time",
    "timestamp": "time",
}


def split_payload_lines(raw: str) -> list[str]:
    text = str(raw or "").replace("\x00", "").strip()
    if not text:
        return []
    return [line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip()]


def normalize_header_token(value: str) -> str:
    return re.sub(r"[^a-z0-9~]+", "", str(value or "").strip().lower())


def parse_option_pairs(raw: str, *, lowercase_keys: bool = False) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in split_payload_lines(raw):
        separator = "\t" if "\t" in line and "," not in line else ","
        for part in [piece.strip() for piece in line.split(separator) if piece.strip()]:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            key_txt = str(key or "").strip()
            if not key_txt:
                continue
            out[key_txt.lower() if lowercase_keys else key_txt] = str(value or "").strip()
    return out


def parse_csv_table(raw: str) -> dict[str, Any]:
    lines = split_payload_lines(raw)
    if not lines:
        return {"has_header": False, "header": [], "rows": [], "header_map": {}}

    header = [part.strip() for part in lines[0].split(",")]
    has_header = any(re.search(r"[A-Za-z~]", col or "") for col in header)
    data_lines = lines[1:] if has_header else lines
    rows: list[dict[str, str]] = []
    header_map: dict[str, int] = {}

    if has_header:
        for idx, column in enumerate(header):
            normalized = normalize_header_token(column)
            if normalized and normalized not in header_map:
                header_map[normalized] = idx
        for line in data_lines:
            parts = [part.strip() for part in line.split(",")]
            row: dict[str, str] = {}
            for idx, column in enumerate(header):
                row[str(column or "").strip()] = parts[idx] if idx < len(parts) else ""
            rows.append(row)

    return {
        "has_header": has_header,
        "header": header if has_header else [],
        "rows": rows,
        "header_map": header_map,
    }


def _canonicalize_row(row: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in row.items():
        alias = _HEADER_ALIASES.get(normalize_header_token(key))
        if alias:
            out[alias] = str(value or "").strip()
    return out


def decode_user_rows(raw: str) -> list[dict[str, str]]:
    table = parse_csv_table(raw)
    if not table.get("has_header"):
        return []
    decoded: list[dict[str, str]] = []
    for row in table.get("rows") or []:
        item = _canonicalize_row(row)
        if any(str(value or "").strip() for value in item.values()):
            decoded.append(item)
    return decoded


def _looks_like_epoch(value: str) -> bool:
    value = str(value or "").strip()
    return bool(re.fullmatch(r"\d{8,}", value))


def _decode_transaction_parts(parts: list[str]) -> dict[str, str]:
    if len(parts) >= 6 and re.match(r"^\d{4}-\d{2}-\d{2}", parts[0] or ""):
        return {
            "time": parts[0],
            "pin": parts[1] if len(parts) > 1 else "",
            "cardno": parts[2] if len(parts) > 2 else "",
            "door_id": parts[3] if len(parts) > 3 else "",
            "event_type": parts[4] if len(parts) > 4 else "",
            "verified": parts[5] if len(parts) > 5 else "",
            "source_format": "timestamp-led",
        }
    if len(parts) == 9:
        return {
            "pin": parts[0],
            "verified": parts[1],
            "door_id": parts[2],
            "event_type": parts[3],
            "in_out_state": parts[4],
            "time_second": parts[5],
            "index": parts[6],
            "cardno": parts[7],
            "sitecode": parts[8],
            "source_format": "rtlog-pin-first-9",
        }
    if len(parts) == 8:
        if _looks_like_epoch(parts[6]) and (parts[7].isdigit() or not parts[7]):
            return {
                "cardno": parts[0],
                "pin": parts[1],
                "verified": parts[2],
                "door_id": parts[3],
                "event_type": parts[4],
                "in_out_state": parts[5],
                "time_second": parts[6],
                "index": parts[7],
                "source_format": "transaction-cardno-first-8",
            }
        return {
            "pin": parts[0],
            "verified": parts[1],
            "door_id": parts[2],
            "event_type": parts[3],
            "in_out_state": parts[4],
            "time_second": parts[5],
            "cardno": parts[6],
            "sitecode": parts[7],
            "source_format": "rtlog-pin-first-8",
        }
    if len(parts) == 7:
        return {
            "cardno": parts[0],
            "pin": parts[1],
            "verified": parts[2],
            "door_id": parts[3],
            "event_type": parts[4],
            "in_out_state": parts[5],
            "time_second": parts[6],
            "source_format": "transaction-cardno-first-7",
        }
    return {"raw": ",".join(parts), "source_format": "unknown"}


def decode_transaction_rows(raw: str) -> list[dict[str, str]]:
    lines = split_payload_lines(raw)
    if not lines:
        return []

    table = parse_csv_table(raw)
    decoded: list[dict[str, str]] = []
    if table.get("has_header"):
        for row in table.get("rows") or []:
            item = _canonicalize_row(row)
            if any(str(value or "").strip() for value in item.values()):
                item.setdefault("source_format", "header-driven")
                decoded.append(item)
        if decoded:
            return decoded

    for line in lines:
        low = line.lower().replace(" ", "")
        if low.startswith("pin,") or low.startswith("cardno,"):
            continue
        if "=" in line:
            kv = {normalize_header_token(k): v for k, v in parse_option_pairs(line).items()}
            item = {
                "cardno": kv.get("cardno", kv.get("transactioncardno", kv.get("card", ""))),
                "pin": kv.get("pin", ""),
                "verified": kv.get("verified", ""),
                "door_id": kv.get("doorid", kv.get("door", "")),
                "event_type": kv.get("eventtype", kv.get("event", "")),
                "in_out_state": kv.get("inoutstate", kv.get("inout", "")),
                "time_second": kv.get("timesecond", kv.get("time", "")),
                "index": kv.get("index", kv.get("id", kv.get("logid", ""))),
                "sitecode": kv.get("sitecode", ""),
                "source_format": "key-value",
            }
            if any(str(value or "").strip() for key, value in item.items() if key != "source_format"):
                decoded.append(item)
            continue
        decoded.append(_decode_transaction_parts([part.strip() for part in line.split(",")]))
    return [row for row in decoded if any(str(value or "").strip() for key, value in row.items() if key != "source_format")]


def preview_rows(rows: list[dict[str, str]], *, max_rows: int = 2) -> list[dict[str, str]]:
    return [dict(item) for item in list(rows or [])[: max(1, int(max_rows or 1))]]
