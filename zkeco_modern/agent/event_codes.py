"""Legacy-oriented event / verify-mode mapping.

Both RTLog and "new log" downloads use a CSV-ish line format in this project:

  ts,pin,card,door,event_code,verify_mode,...

Legacy UI expects:
- **Event Description** values (e.g. "Door Opened Correctly", "Remote Opening")
- **Verify Mode** values (e.g. "Only Card", "Card Plus Password", ...)

This module centralizes the mapping so reports and realtime monitoring can stay
consistent.
"""

from __future__ import annotations

from typing import Dict


# Event code -> legacy label
# NOTE: Device firmwares vary a lot; we only map codes we actually emit/observe.
EVENT_CODES: Dict[str, str] = {
    # Door state (used by our code paths)
    "100": "Door Opened Correctly",
    "101": "Door Closed Correctly",

    # Access result (used by our code paths)
    "200": "Access Granted",
    "201": "Access Denied",

    # Alarms (placeholder; adjust as you catalog codes)
    "300": "Alarm Triggered",
    "301": "Alarm Cleared",

    # A few known legacy event ids seen in translations
    "203": "Multi-Card Open(Card plus Fingerprint)",
}


# Verify mode numeric codes -> legacy label.
# These labels come from the legacy locale/help files bundled with the repo.
# If a device uses different numeric codes, we fall back safely.
VERIFY_MODE_CODES: Dict[str, str] = {
    "0": "Only Card",
    "1": "Only Fingerprint",
    "2": "Card or Fingerprint",
    "3": "Card plus Fingerprint",
    "4": "Card Plus Password",
    "5": "Card or Password",
    "6": "Only Password",
    "7": "Fingerprint plus Password",
    "8": "Fingerprint or Password",
    "9": "Card plus Fingerprint plus Password",
    "10": "Card or Password or Fingerprint",
    "11": "Only Pin",
    "12": "Pin and Fingerprint",
    "13": "Pin and Password and Fingerprint",
    "14": "Pin and Fingerprint or Card and Fingerprint",
    "15": "Password and Fingerprint or Card and Fingerprint",
}


DOOR_EVENT_LABELS: Dict[str, str] = {
    "door.open": "Remote Opening",
    "door.close": "Remote Closing",
    "door.normal_open": "Remote Normal Opening",
    "door.cancel_alarm": "Cancel Alarm",
    "door.lock": "Lock",
    "door.unlock": "Unlock",
}


def describe(code: str) -> str:
    """Map an event code to a legacy-like description."""
    return EVENT_CODES.get(str(code).strip(), "")


def describe_verify_mode(raw_verify_mode: str) -> str:
    """Map device verify-mode field into a legacy label.

    - Empty/None is treated as default "Only Card".
    - Unknown numeric values are returned as "Verify Mode <n>".
    - Non-numeric values (e.g. internal sources like "API") are passed through.
    """
    s = str(raw_verify_mode or "").strip()
    if s == "":
        return "Only Card"
    # Common internal source labels that should map to legacy verify labels.
    src_upper = s.upper()
    if src_upper in ("CITITOR FIZIC", "PHYSICAL READER", "READER"):
        return "Only Card"
    if src_upper in ("TEST", "UNKNOWN"):
        return "Others"

    if s in VERIFY_MODE_CODES:
        return VERIFY_MODE_CODES[s]
    if s.isdigit():
        return f"Verify Mode {s}"
    return s


def describe_door_event_type(event_type: str) -> str:
    """Map our WebSocket door.* event types to legacy-friendly descriptions."""
    return DOOR_EVENT_LABELS.get(str(event_type or "").strip(), str(event_type or "").strip())