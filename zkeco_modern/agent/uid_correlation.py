from __future__ import annotations

import re
import time
from typing import Any, Optional

from django.core.cache import cache
from django.utils import timezone


BUFFER_TTL_S = 30.0
MATCH_WINDOW_S = 15.0
MAX_BUCKET_ITEMS = 12

_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")


def sanitize_card_number(value: Any) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "", str(value or "")).upper()


def normalize_door_number(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return str(int(text))
    except Exception:
        return text


def _bucket_key(device_id: int, door_number: str) -> str:
    return f"agent:uid-correlation:{int(device_id or 0)}:{door_number or '*'}"


def _store_keys(device_id: int, door_number: str) -> list[str]:
    dev_id = int(device_id or 0)
    if dev_id <= 0:
        return []
    door = normalize_door_number(door_number)
    keys = [_bucket_key(dev_id, "*")]
    if door:
        keys.insert(0, _bucket_key(dev_id, door))
    return keys


def _prune_bucket(items: Any, *, now_ts: float, max_age_s: float = BUFFER_TTL_S) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in list(items or []):
        if not isinstance(item, dict):
            continue
        try:
            observed_ts = float(item.get("observed_ts") or 0.0)
        except Exception:
            observed_ts = 0.0
        if observed_ts <= 0.0:
            continue
        age_s = now_ts - observed_ts
        if age_s < -2.0 or age_s > float(max_age_s):
            continue
        out.append(dict(item))
    return out[:MAX_BUCKET_ITEMS]


def remember_sniffed_uid(
    *,
    device_id: int,
    door_number: Any,
    card_number: Any,
    source: str,
    payload: Optional[dict[str, Any]] = None,
) -> dict[str, Any] | None:
    dev_id = int(device_id or 0)
    card = sanitize_card_number(card_number)
    if dev_id <= 0 or not card:
        return None

    now_ts = time.time()
    door = normalize_door_number(door_number)
    entry = {
        "entry_id": f"{int(now_ts * 1000)}:{dev_id}:{door or '*'}:{card}",
        "device_id": dev_id,
        "door_number": door,
        "card_number": card,
        "source": str(source or "").strip() or "wiegand",
        "observed_ts": now_ts,
        "observed_at": timezone.now().isoformat(),
        "payload": dict(payload or {}),
    }

    for key in _store_keys(dev_id, door):
        items = _prune_bucket(cache.get(key), now_ts=now_ts)
        items = [item for item in items if str(item.get("entry_id") or "") != entry["entry_id"]]
        items.insert(0, dict(entry))
        cache.set(key, items[:MAX_BUCKET_ITEMS], timeout=int(BUFFER_TTL_S * 2))
    return entry


def resolve_controller_uid(*, device_id: int, door_number: Any, match_window_s: float = MATCH_WINDOW_S) -> dict[str, Any] | None:
    dev_id = int(device_id or 0)
    if dev_id <= 0:
        return None

    door = normalize_door_number(door_number)
    now_ts = time.time()
    best: dict[str, Any] | None = None
    best_age_s: float | None = None
    matched_entry_id = ""

    for key in _store_keys(dev_id, door):
        items = _prune_bucket(cache.get(key), now_ts=now_ts)
        for item in items:
            card = sanitize_card_number(item.get("card_number"))
            if not card:
                continue
            item_door = normalize_door_number(item.get("door_number"))
            if door and item_door and item_door != door:
                continue
            try:
                age_s = max(0.0, now_ts - float(item.get("observed_ts") or 0.0))
            except Exception:
                age_s = float(match_window_s) + 1.0
            if age_s > float(match_window_s):
                continue
            if best_age_s is None or age_s < best_age_s:
                best_age_s = age_s
                matched_entry_id = str(item.get("entry_id") or "")
                best = {
                    "resolved_from_wiegand": True,
                    "resolution_source": "wiegand_buffer",
                    "device_id": dev_id,
                    "door_number": door or item_door,
                    "sniffed_card_number": card,
                    "sniffed_source": str(item.get("source") or ""),
                    "sniffed_at": str(item.get("observed_at") or ""),
                    "buffer_age_ms": int(age_s * 1000.0),
                    "buffer_entry_id": matched_entry_id,
                    "buffer_payload": dict(item.get("payload") or {}),
                }

    if not best or not matched_entry_id:
        return None

    for key in _store_keys(dev_id, door):
        items = _prune_bucket(cache.get(key), now_ts=now_ts)
        items = [item for item in items if str(item.get("entry_id") or "") != matched_entry_id]
        cache.set(key, items[:MAX_BUCKET_ITEMS], timeout=int(BUFFER_TTL_S * 2))
    return best


def inject_card_number_into_rtlog(raw_line: str, card_number: Any) -> str:
    card = sanitize_card_number(card_number)
    raw = str(raw_line or "").strip()
    if not raw or not card:
        return raw

    parts = [part.strip() for part in raw.split(",")]
    if len(parts) >= 6 and _TS_RE.match(parts[0] or ""):
        card_idx = 2
    elif len(parts) >= 9:
        card_idx = 7
    elif len(parts) >= 8:
        card_idx = 6
    else:
        return raw
    while len(parts) <= card_idx:
        parts.append("")
    parts[card_idx] = card
    return ",".join(parts)