"""Event code mapping.

This lightweight dictionary maps numeric event codes (as strings) to
human-readable short descriptions. Extend as real codes are cataloged.

Legacy systems often used codes in the 100..600 range for access and
alarm events. Populate incrementally from observed raw lines.
"""

EVENT_CODES = {
    "100": "Door Open",
    "101": "Door Close",
    "200": "Access Granted",
    "201": "Access Denied",
    "300": "Alarm Triggered",
    "301": "Alarm Cleared",
    # Placeholder examples; replace with authoritative mapping.
}

def describe(code: str) -> str:
    return EVENT_CODES.get(code, "")