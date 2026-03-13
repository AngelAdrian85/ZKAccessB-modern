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
# NOTE: Device firmwares vary a lot. For C3/F3/G controller eventType values we
# prefer the bundled ZKAccess 3.5 language tables (`LinkAgeIO`) over guesswork.
# App-internal synthetic result codes may still exist elsewhere in the UI.
EVENT_CODES: Dict[str, str] = {
    # ---------------------------------------------------------------
    # ZKTeco C3/F3/G series Format B transaction eventType codes (0-39)
    # These appear in the eventType (index 3) field of Format B lines:
    #   pin,verified,door,eventType,inOut,time_second[,index][,cardno,sitecode]
    # ---------------------------------------------------------------
    "0": "Normal Punch Open",
    "1": "Punch during Passage Mode Time Zone",
    "2": "First-Card Normal Open(Punch Card)",
    "3": "Multi-Card Open(Punch Card)",
    "4": "Emergency Password Open",
    "5": "Open during Passage Mode Time Zone",
    "8": "Remote Opening",
    "9": "Remote Closing",
    "14": "Normal Fingerprint Open",
    "15": "Multi-Card Open(Press Fingerprint)",
    "16": "Press Fingerprint during Passage Mode Time Zone",
    "17": "Card plus Fingerprint Open",
    "18": "First-Card Normal Open(Press Fingerprint)",
    "19": "First-Card Normal Open(Card plus Fingerprint)",
    "20": "Punch Interval too Short",
    "21": "Door Inactive Time Zone(Punch Card)",
    "22": "Illegal Time Zone",
    "23": "Access Denied",
    "24": "Anti-Passback",
    "25": "Interlock",
    "26": "Multi-Card Authentication(Punch Card)",
    "27": "Access denied - Unregistered Card",
    "28": "Open Door Time Out",
    "29": "Card Expired",
    "30": "Password Error",
    "31": "Press Fingerprint Interval too Short",
    "32": "Multi-Card Authentication(Press Fingerprint)",
    "33": "Fingerprint Expired",
    "34": "Access denied - Unregistered Fingerprint",
    "35": "Door Inactive Time Zone(Press Fingerprint)",
    "36": "Door Inactive Time Zone(Press Exit Button)",
    "37": "Failed to Close during Passage Mode Time Zone",
    "255": "Access denied - Unregistered Card",

    # ---------------------------------------------------------------
    # Door state (used by our code paths)
    # ---------------------------------------------------------------
    "100": "Door Opened Correctly",
    "101": "Door Closed Correctly",
    "102": "Opened Forcefully",
    "103": "Duress Fingerprint Open",

    # ---------------------------------------------------------------
    # Access result (used by our code paths)
    # ---------------------------------------------------------------
    "200": "Door Opened Correctly",
    "201": "Door Closed Correctly",
    "202": "Exit Button Open",
    "203": "Multi-Card Open(Card plus Fingerprint)",
    "204": "Passage Mode Time Zone Over",
    "205": "Remote Normal Opening",

    # ---------------------------------------------------------------
    # Alarms (placeholder; adjust as you catalog codes)
    # ---------------------------------------------------------------
    "300": "Alarm Triggered",
    "301": "Alarm Cleared",

    # ---------------------------------------------------------------
    # A few known legacy event ids seen in translations
    # ---------------------------------------------------------------
    "220": "Auxiliary Input Disconnected",
    "221": "Auxiliary Input Shorted",
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
    "door.normal_close": "Remote Normal Closing",
    "door.cancel_alarm": "Cancel Alarm",
    "door.lock": "Lock",
    "door.unlock": "Unlock",
}


ACCESS_GRANTED_EVENT_CODES = {
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "14",
    "15",
    "16",
    "17",
    "18",
    "19",
    "26",
}


ACCESS_DENIED_EVENT_CODES = {
    "20",
    "21",
    "22",
    "23",
    "24",
    "25",
    "27",
    "28",
    "29",
    "30",
    "31",
    "34",
    "35",
    "36",
    "37",
    "255",
}


DOOR_STATE_EVENT_CODES = {
    "100",
    "101",
    "102",
    "103",
    "200",
    "201",
    "202",
    "203",
    "204",
    "205",
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


def normalized_status_text(code: str, description: str = "") -> str:
    """Classify controller event rows into ACCEPTAT/RESPINS only when semantically valid.

    Door-state notifications like 200/201 should stay as events, not synthetic access
    results, so they return an empty status.
    """
    event_code = str(code or "").strip()
    desc = str(description or "").strip().lower()

    if event_code in DOOR_STATE_EVENT_CODES:
        return ""
    if event_code in ACCESS_GRANTED_EVENT_CODES:
        return "ACCEPTAT"
    if event_code in ACCESS_DENIED_EVENT_CODES:
        return "RESPINS"
    if "access denied" in desc or "unregistered" in desc:
        return "RESPINS"
    return ""


def normalized_access_action(code: str, description: str = "") -> str:
    """Return scan/event classification for controller-derived rows."""
    return "scan" if normalized_status_text(code, description) in ("ACCEPTAT", "RESPINS") else "event"