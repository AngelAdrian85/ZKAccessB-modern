from __future__ import annotations

import datetime as _dt
import re
from typing import Any, Callable, Dict, Optional

from .controller_decoders import decode_transaction_rows
from .event_codes import describe as describe_event_code
from .event_codes import describe_verify_mode


def sanitize_card_value(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "", str(value or "")).upper()


def _decode_time_value(decoded: Dict[str, Any]) -> Optional[_dt.datetime]:
    time_txt = str(decoded.get("time") or "").strip()
    if time_txt:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%d.%m.%Y, %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
            try:
                return _dt.datetime.strptime(time_txt, fmt)
            except Exception:
                continue
    time_second = str(decoded.get("time_second") or "").strip()
    if time_second:
        try:
            secs = int(float(time_second))
            return _dt.datetime(2000, 1, 1, 0, 0, 0) + _dt.timedelta(seconds=secs)
        except Exception:
            return None
    return None


def _is_external_reader_row(raw_line: str, decoded: Dict[str, Any]) -> bool:
    raw_low = str(raw_line or "").lower()
    verify_low = str(decoded.get("verified") or "").lower()
    source_low = str(decoded.get("source_format") or "").lower()
    return (
        "cititor extern" in raw_low
        or ",acp" in raw_low
        or ",elatec" in raw_low
        or ",wiegand" in raw_low
        or "reader" in raw_low
        or "cititor" in verify_low
        or "reader" in verify_low
        or source_low == "timestamp-led"
    )


def _find_recent_external_card(*, device_id: int, door_number: str, event_time: Optional[_dt.datetime]) -> Optional[Dict[str, str]]:
    if not int(device_id or 0):
        return None
    if event_time is None:
        return None

    try:
        from .models import DeviceRealtimeLog
    except Exception:
        return None

    try:
        candidates = list(
            DeviceRealtimeLog.objects.filter(device_id=int(device_id or 0))
            .order_by("-created_at")
            .values("id", "raw")[:40]
        )
    except Exception:
        return None

    best: Optional[Dict[str, str]] = None
    best_delta: Optional[float] = None
    wanted_door = str(door_number or "").strip()

    def _time_delta_seconds(left: _dt.datetime, right: _dt.datetime) -> float:
        direct = abs((left - right).total_seconds())
        if direct <= 5.0:
            return direct
        if abs((left.date() - right.date()).days) <= 1:
            return direct
        left_secs = left.hour * 3600 + left.minute * 60 + left.second
        right_secs = right.hour * 3600 + right.minute * 60 + right.second
        tod = abs(left_secs - right_secs)
        return float(min(tod, 86400 - tod))

    for row in candidates:
        raw = str((row or {}).get("raw") or "").strip()
        if not raw:
            continue
        decoded_rows = decode_transaction_rows(raw)
        if not decoded_rows:
            continue
        decoded = dict(decoded_rows[0])
        if not _is_external_reader_row(raw, decoded):
            continue
        card = sanitize_card_value(decoded.get("cardno", ""))
        if not card or card in {"0", "000000", "0000000", "00000000"}:
            continue
        candidate_door = str(decoded.get("door_id") or "").strip()
        if wanted_door and candidate_door and candidate_door != wanted_door:
            continue
        candidate_time = _decode_time_value(decoded)
        if candidate_time is None:
            continue
        delta = _time_delta_seconds(candidate_time, event_time)
        if delta > 15.0:
            continue
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best = {
                "card": card,
                "delta_seconds": f"{delta:.3f}",
                "source": "external_reader_recent",
                "door_number": candidate_door,
            }
    return best


def build_rtlog_entry(
    raw_line: str,
    *,
    device_id: int = 0,
    serial_number: str = "",
    lookup_card_for_pin: Optional[Callable[[str], str]] = None,
) -> Optional[Dict[str, Any]]:
    raw_line = str(raw_line or "").strip()
    if not raw_line:
        return None

    decoded_rows = decode_transaction_rows(raw_line)
    if not decoded_rows:
        return None
    decoded = dict(decoded_rows[0])

    pin = str(decoded.get("pin") or "").strip()
    card = sanitize_card_value(decoded.get("cardno", ""))
    raw_card = card
    enrichment_source = ""
    enrichment_status = "controller"
    enrichment_note = ""

    index_hint = sanitize_card_value(decoded.get("index", ""))
    if (not card or card == "0") and index_hint:
        if (not index_hint.isdigit()) or len(index_hint) >= 7:
            card = index_hint
            raw_card = index_hint
            enrichment_source = "rtlog.index"
            enrichment_status = "derived"

    if (not card or card == "0") and pin and pin not in ("0", "") and lookup_card_for_pin:
        looked_up = sanitize_card_value(lookup_card_for_pin(pin))
        if looked_up and looked_up not in {"0", "000000", "0000000", "00000000"}:
            card = looked_up
            raw_card = looked_up
            enrichment_source = "panel_user_map"
            enrichment_status = "enriched"

    event_time = _decode_time_value(decoded)
    if (not card or card == "0") and int(device_id or 0):
        external_match = _find_recent_external_card(
            device_id=int(device_id or 0),
            door_number=str(decoded.get("door_id") or "").strip(),
            event_time=event_time,
        )
        if external_match:
            matched_card = sanitize_card_value(external_match.get("card", ""))
            if matched_card and matched_card not in {"0", "000000", "0000000", "00000000"}:
                card = matched_card
                raw_card = matched_card
                enrichment_source = str(external_match.get("source") or "external_reader_recent")
                enrichment_status = "enriched"
                enrichment_note = f"recent_external_reader_card_match door={external_match.get('door_number') or ''} delta_s={external_match.get('delta_seconds') or ''}".strip()

    controller_event_status = ""
    controller_event_without_cardno = False
    card_display_status = ""
    card_display_label = ""
    card_display_note = ""
    if not card or card in {"0", "000000", "0000000", "00000000"}:
        card = ""
        raw_card = ""
        enrichment_status = "unresolved"
        enrichment_note = "controller_rtlog_missing_pin_and_cardno" if pin in ("", "0") else "panel_user_map_miss"
        controller_event_status = "controller-event-without-cardno"
        controller_event_without_cardno = True
        card_display_status = "valid_without_cardno"
        card_display_label = "Valid fara CardNo"
        card_display_note = "Eveniment valid raportat de controller; firmware-ul nu a trimis CardNo pe acest canal."

    event_type = str(decoded.get("event_type") or "").strip()
    verify_code = str(decoded.get("verified") or "").strip()
    return {
        "raw": raw_line,
        "device_id": int(device_id or 0),
        "serial_number": str(serial_number or ""),
        "source_format": str(decoded.get("source_format") or ""),
        "pin": pin,
        "door_number": str(decoded.get("door_id") or "").strip(),
        "event_code": event_type,
        "event_description": describe_event_code(event_type),
        "verify_code": verify_code,
        "verify_mode": describe_verify_mode(verify_code),
        "time": str(decoded.get("time") or "").strip(),
        "time_second": str(decoded.get("time_second") or "").strip(),
        "index": str(decoded.get("index") or "").strip(),
        "sitecode": str(decoded.get("sitecode") or "").strip(),
        "card_no": card,
        "card_no_raw": raw_card,
        "enrichment_source": enrichment_source,
        "enrichment_status": enrichment_status,
        "enrichment_note": enrichment_note,
        "card_lookup_key": pin if pin not in ("", "0") else "unavailable",
        "controller_event_status": controller_event_status,
        "controller_event_without_cardno": controller_event_without_cardno,
        "card_display_status": card_display_status,
        "card_display_label": card_display_label,
        "card_display_note": card_display_note,
    }
