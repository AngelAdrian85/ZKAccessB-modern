from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any


@dataclass(frozen=True)
class WiegandFormat:
    name: str
    bit_length: int
    odd_parity_start: int = 0
    odd_parity_count: int = 0
    even_parity_start: int = 0
    even_parity_count: int = 0
    cid_start: int = 0
    cid_count: int = 0
    facility_code_start: int = 0
    facility_code_count: int = 0
    site_code_start: int = 0
    site_code_count: int = 0
    manufactory_code_start: int = 0
    manufactory_code_count: int = 0
    wiegand_mode: int = 1
    first_p: int = 0
    second_p: int = 0
    before_fmt: str = ""
    after_fmt: str = ""
    default: bool = False


_DEFAULT_FORMATS: tuple[WiegandFormat, ...] = (
    WiegandFormat(
        name="Wiegand 26",
        bit_length=26,
        odd_parity_start=14,
        odd_parity_count=13,
        even_parity_start=1,
        even_parity_count=13,
        cid_start=2,
        cid_count=24,
        default=True,
    ),
    WiegandFormat(
        name="Wiegand 26a",
        bit_length=26,
        odd_parity_start=14,
        odd_parity_count=13,
        even_parity_start=1,
        even_parity_count=13,
        cid_start=10,
        cid_count=16,
        facility_code_start=2,
        facility_code_count=8,
    ),
    WiegandFormat(
        name="Wiegand 34",
        bit_length=34,
        odd_parity_start=18,
        odd_parity_count=17,
        even_parity_start=1,
        even_parity_count=17,
        cid_start=2,
        cid_count=32,
        default=True,
    ),
    WiegandFormat(
        name="Wiegand 34a",
        bit_length=34,
        odd_parity_start=18,
        odd_parity_count=17,
        even_parity_start=1,
        even_parity_count=17,
        cid_start=18,
        cid_count=16,
        site_code_start=2,
        site_code_count=16,
    ),
    WiegandFormat(
        name="Wiegand 35",
        bit_length=35,
        odd_parity_start=19,
        odd_parity_count=17,
        even_parity_start=1,
        even_parity_count=18,
        cid_start=15,
        cid_count=20,
        site_code_start=2,
        site_code_count=13,
        default=True,
    ),
    WiegandFormat(
        name="Wiegand 36",
        bit_length=36,
        odd_parity_start=1,
        odd_parity_count=15,
        even_parity_start=16,
        even_parity_count=21,
        cid_start=18,
        cid_count=18,
        site_code_start=2,
        site_code_count=16,
        default=True,
    ),
    WiegandFormat(
        name="Wiegand 37",
        bit_length=37,
        odd_parity_start=19,
        odd_parity_count=19,
        even_parity_start=1,
        even_parity_count=18,
        cid_start=21,
        cid_count=16,
        facility_code_start=5,
        facility_code_count=10,
        site_code_start=15,
        site_code_count=6,
        manufactory_code_start=2,
        manufactory_code_count=3,
        default=True,
    ),
    WiegandFormat(
        name="Wiegand 37a",
        bit_length=37,
        odd_parity_start=19,
        odd_parity_count=19,
        even_parity_start=1,
        even_parity_count=18,
        cid_start=18,
        cid_count=19,
        site_code_start=6,
        site_code_count=12,
        manufactory_code_start=2,
        manufactory_code_count=4,
    ),
    WiegandFormat(
        name="Wiegand 50",
        bit_length=50,
        odd_parity_start=26,
        odd_parity_count=25,
        even_parity_start=1,
        even_parity_count=25,
        cid_start=18,
        cid_count=32,
        site_code_start=2,
        site_code_count=16,
        default=True,
    ),
    WiegandFormat(
        name="Wiegand 66",
        bit_length=66,
        odd_parity_start=34,
        odd_parity_count=33,
        even_parity_start=1,
        even_parity_count=33,
        cid_start=2,
        cid_count=64,
        default=True,
    ),
)


_FORMATS_BY_KEY = {re.sub(r"[^a-z0-9]+", "", fmt.name.lower()): fmt for fmt in _DEFAULT_FORMATS}
_FORMATS_BY_LENGTH: dict[int, list[WiegandFormat]] = {}
for _fmt in _DEFAULT_FORMATS:
    _FORMATS_BY_LENGTH.setdefault(int(_fmt.bit_length), []).append(_fmt)


def _normalize_format_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or str(value).strip() == "":
            return int(default)
        return int(str(value).strip())
    except Exception:
        return int(default)


def _normalize_pattern(value: Any, bit_length: int = 0) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "", str(value or "").strip()).lower()
    if bit_length > 0 and text and len(text) < bit_length:
        text = text.ljust(bit_length, "0")
    return text


def _span_from_pattern(pattern: str, chars: str) -> tuple[int, int]:
    positions = [idx + 1 for idx, ch in enumerate(str(pattern or "").lower()) if ch in chars]
    if not positions:
        return 0, 0
    return positions[0], len(positions)


def _render_pattern(bit_length: int, spans: list[tuple[str, int, int]]) -> str:
    count = max(0, int(bit_length or 0))
    if count <= 0:
        return ""
    chars = ["0"] * count
    for marker, start, length in spans:
        if int(start or 0) <= 0 or int(length or 0) <= 0:
            continue
        begin = int(start) - 1
        end = min(count, begin + int(length))
        for idx in range(begin, end):
            chars[idx] = str(marker or "0")[:1]
    return "".join(chars)


def build_format_patterns(fmt: WiegandFormat) -> tuple[str, str]:
    before_fmt = _normalize_pattern(fmt.before_fmt, int(fmt.bit_length))
    after_fmt = _normalize_pattern(fmt.after_fmt, int(fmt.bit_length))
    if not before_fmt:
        before_fmt = _render_pattern(
            fmt.bit_length,
            [
                ("p", fmt.first_p, 1),
                ("p", fmt.second_p, 1),
                ("c", fmt.cid_start, fmt.cid_count),
                ("f", fmt.facility_code_start, fmt.facility_code_count),
                ("s", fmt.site_code_start, fmt.site_code_count),
                ("m", fmt.manufactory_code_start, fmt.manufactory_code_count),
            ],
        )
    if not after_fmt:
        after_fmt = _render_pattern(
            fmt.bit_length,
            [
                ("e", fmt.even_parity_start, fmt.even_parity_count),
                ("o", fmt.odd_parity_start, fmt.odd_parity_count),
                ("c", fmt.cid_start, fmt.cid_count),
                ("f", fmt.facility_code_start, fmt.facility_code_count),
                ("s", fmt.site_code_start, fmt.site_code_count),
                ("m", fmt.manufactory_code_start, fmt.manufactory_code_count),
            ],
        )
    return before_fmt, after_fmt


def format_to_dict(fmt: WiegandFormat) -> dict[str, Any]:
    payload = asdict(fmt)
    before_fmt, after_fmt = build_format_patterns(fmt)
    payload["before_fmt"] = before_fmt
    payload["after_fmt"] = after_fmt
    payload["format_name"] = fmt.name
    payload["wiegand_count"] = fmt.bit_length
    return payload


def list_known_wiegand_formats(*, include_details: bool = False) -> list[dict[str, Any]]:
    items = []
    for fmt in _DEFAULT_FORMATS:
        row = {
            "name": fmt.name,
            "bit_length": fmt.bit_length,
            "default": fmt.default,
        }
        if include_details:
            row.update(format_to_dict(fmt))
        items.append(row)
    return items


def get_wiegand_format(name: str | None = None, *, bit_length: int | None = None) -> WiegandFormat | None:
    if name:
        return _FORMATS_BY_KEY.get(_normalize_format_name(name))
    if bit_length is None:
        return None
    candidates = list(_FORMATS_BY_LENGTH.get(int(bit_length), []))
    if not candidates:
        return None
    for fmt in candidates:
        if fmt.default:
            return fmt
    return candidates[0]


def _coerce_bit_length(bit_length: Any) -> int | None:
    try:
        if bit_length is None or str(bit_length).strip() == "":
            return None
        value = int(str(bit_length).strip())
        return value if value > 0 else None
    except Exception:
        return None


def build_wiegand_format_from_mapping(mapping: Any) -> WiegandFormat:
    if isinstance(mapping, WiegandFormat):
        return mapping
    if not isinstance(mapping, dict):
        raise ValueError("format_data must be a mapping")

    name = (
        str(mapping.get("name") or mapping.get("format_name") or mapping.get("wiegand_name") or "Custom Wiegand")
        .strip()
        or "Custom Wiegand"
    )
    before_fmt_raw = _normalize_pattern(mapping.get("before_fmt") or mapping.get("card_fmt"))
    after_fmt_raw = _normalize_pattern(mapping.get("after_fmt") or mapping.get("parity_fmt"))
    bit_length = _coerce_bit_length(mapping.get("bit_length") or mapping.get("wiegand_count"))
    if bit_length is None:
        bit_length = len(before_fmt_raw) or len(after_fmt_raw) or 0
    if bit_length <= 0:
        raise ValueError("bit_length required")

    mode = _coerce_int(mapping.get("wiegand_mode"), 1)
    if mode not in (1, 2):
        mode = 1
    if mode == 1 and before_fmt_raw and after_fmt_raw and not any(
        _coerce_int(mapping.get(key), 0)
        for key in (
            "cid_start",
            "cid_count",
            "facility_code_start",
            "facility_code_count",
            "site_code_start",
            "site_code_count",
            "manufactory_code_start",
            "manufactory_code_count",
            "even_parity_start",
            "even_parity_count",
            "odd_parity_start",
            "odd_parity_count",
        )
    ):
        mode = 2

    if mode == 2:
        cid_start, cid_count = _span_from_pattern(before_fmt_raw or after_fmt_raw, "c")
        facility_start, facility_count = _span_from_pattern(before_fmt_raw or after_fmt_raw, "f")
        site_start, site_count = _span_from_pattern(before_fmt_raw or after_fmt_raw, "s")
        manufactory_start, manufactory_count = _span_from_pattern(before_fmt_raw or after_fmt_raw, "m")
        even_start, even_count = _span_from_pattern(after_fmt_raw, "e")
        odd_start, odd_count = _span_from_pattern(after_fmt_raw, "o")
        first_p, _ = _span_from_pattern(before_fmt_raw, "p")
        second_p = 0
        if first_p > 0:
            remaining = [idx + 1 for idx, ch in enumerate(before_fmt_raw) if ch == "p" and (idx + 1) != first_p]
            second_p = remaining[0] if remaining else 0
    else:
        cid_start = _coerce_int(mapping.get("cid_start"), 0)
        cid_count = _coerce_int(mapping.get("cid_count"), 0)
        facility_start = _coerce_int(mapping.get("facility_code_start"), 0)
        facility_count = _coerce_int(mapping.get("facility_code_count"), 0)
        site_start = _coerce_int(mapping.get("site_code_start"), 0)
        site_count = _coerce_int(mapping.get("site_code_count"), 0)
        manufactory_start = _coerce_int(mapping.get("manufactory_code_start"), 0)
        manufactory_count = _coerce_int(mapping.get("manufactory_code_count"), 0)
        even_start = _coerce_int(mapping.get("even_parity_start"), 0)
        even_count = _coerce_int(mapping.get("even_parity_count"), 0)
        odd_start = _coerce_int(mapping.get("odd_parity_start"), 0)
        odd_count = _coerce_int(mapping.get("odd_parity_count"), 0)
        first_p = _coerce_int(mapping.get("first_p"), 0)
        second_p = _coerce_int(mapping.get("second_p"), 0)

    fmt = WiegandFormat(
        name=name,
        bit_length=int(bit_length),
        odd_parity_start=odd_start,
        odd_parity_count=odd_count,
        even_parity_start=even_start,
        even_parity_count=even_count,
        cid_start=cid_start,
        cid_count=cid_count,
        facility_code_start=facility_start,
        facility_code_count=facility_count,
        site_code_start=site_start,
        site_code_count=site_count,
        manufactory_code_start=manufactory_start,
        manufactory_code_count=manufactory_count,
        wiegand_mode=mode,
        first_p=first_p,
        second_p=second_p,
        before_fmt=before_fmt_raw,
        after_fmt=after_fmt_raw,
        default=bool(mapping.get("default")),
    )
    if not fmt.before_fmt or not fmt.after_fmt:
        before_fmt, after_fmt = build_format_patterns(fmt)
        fmt = WiegandFormat(
            **{
                **asdict(fmt),
                "before_fmt": before_fmt,
                "after_fmt": after_fmt,
            }
        )
    return fmt


def normalize_wiegand_bits(
    *,
    bits: Any = None,
    hex_value: Any = None,
    int_value: Any = None,
    bit_length: Any = None,
) -> str:
    target_length = _coerce_bit_length(bit_length)

    bits_txt = re.sub(r"[^01]+", "", str(bits or "").strip())
    if bits_txt:
        if target_length and len(bits_txt) != target_length:
            if len(bits_txt) < target_length:
                bits_txt = bits_txt.zfill(target_length)
            else:
                raise ValueError(f"wiegand_bits length {len(bits_txt)} does not match expected {target_length}")
        return bits_txt

    hex_txt = re.sub(r"[^0-9A-Fa-f]+", "", str(hex_value or "").strip())
    if hex_txt:
        raw_bits = bin(int(hex_txt, 16))[2:]
        if target_length:
            if len(raw_bits) > target_length:
                raise ValueError(f"wiegand_hex expands to {len(raw_bits)} bits which exceeds expected {target_length}")
            raw_bits = raw_bits.zfill(target_length)
        else:
            raw_bits = raw_bits.zfill(len(hex_txt) * 4)
        return raw_bits

    int_txt = str(int_value or "").strip()
    if int_txt:
        if not re.fullmatch(r"[0-9]+", int_txt):
            raise ValueError("wiegand_int must contain only digits")
        raw_bits = bin(int(int_txt, 10))[2:]
        if target_length:
            if len(raw_bits) > target_length:
                raise ValueError(f"wiegand_int expands to {len(raw_bits)} bits which exceeds expected {target_length}")
            raw_bits = raw_bits.zfill(target_length)
        return raw_bits

    raise ValueError("missing Wiegand input")


def _slice_bits(bits: str, start: int, count: int) -> str:
    if start <= 0 or count <= 0:
        return ""
    start_idx = int(start) - 1
    end_idx = start_idx + int(count)
    if start_idx >= len(bits):
        return ""
    return bits[start_idx:end_idx]


def _parse_int(bits: str, start: int, count: int) -> int | None:
    chunk = _slice_bits(bits, start, count)
    if not chunk:
        return None
    return int(chunk, 2)


def _parity_status(bits: str, start: int, count: int, want_even: bool) -> dict[str, Any]:
    chunk = _slice_bits(bits, start, count)
    if not chunk:
        return {"ok": None, "ones": 0, "bits": "", "expected": "even" if want_even else "odd"}
    ones = chunk.count("1")
    ok = (ones % 2 == 0) if want_even else (ones % 2 == 1)
    return {
        "ok": ok,
        "ones": ones,
        "bits": chunk,
        "expected": "even" if want_even else "odd",
    }


def _decode_bits_with_format(raw_bits: str, fmt: WiegandFormat) -> dict[str, Any]:
    card_value = _parse_int(raw_bits, fmt.cid_start, fmt.cid_count)
    facility_value = _parse_int(raw_bits, fmt.facility_code_start, fmt.facility_code_count)
    site_value = _parse_int(raw_bits, fmt.site_code_start, fmt.site_code_count)
    manufacturer_value = _parse_int(raw_bits, fmt.manufactory_code_start, fmt.manufactory_code_count)

    even_parity = _parity_status(raw_bits, fmt.even_parity_start, fmt.even_parity_count, True)
    odd_parity = _parity_status(raw_bits, fmt.odd_parity_start, fmt.odd_parity_count, False)
    parity_values = [p.get("ok") for p in (even_parity, odd_parity) if p.get("ok") is not None]
    parity_ok = all(parity_values) if parity_values else None
    before_fmt, after_fmt = build_format_patterns(fmt)

    return {
        "format_name": fmt.name,
        "bit_length": fmt.bit_length,
        "raw_bits": raw_bits,
        "raw_hex": format(int(raw_bits, 2), f"0{max(1, (len(raw_bits) + 3) // 4)}X"),
        "card_number": "" if card_value is None else str(card_value),
        "card_bits": _slice_bits(raw_bits, fmt.cid_start, fmt.cid_count),
        "facility_code": None if facility_value is None else int(facility_value),
        "facility_bits": _slice_bits(raw_bits, fmt.facility_code_start, fmt.facility_code_count),
        "site_code": None if site_value is None else int(site_value),
        "site_bits": _slice_bits(raw_bits, fmt.site_code_start, fmt.site_code_count),
        "manufacturer_code": None if manufacturer_value is None else int(manufacturer_value),
        "manufacturer_bits": _slice_bits(raw_bits, fmt.manufactory_code_start, fmt.manufactory_code_count),
        "parity_ok": parity_ok,
        "parity": {
            "even": even_parity,
            "odd": odd_parity,
        },
        "wiegand_mode": fmt.wiegand_mode,
        "before_fmt": before_fmt,
        "after_fmt": after_fmt,
        "format": format_to_dict(fmt),
    }


def decode_wiegand(
    *,
    bits: Any = None,
    hex_value: Any = None,
    int_value: Any = None,
    format_name: str | None = None,
    bit_length: Any = None,
    format_data: Any = None,
) -> dict[str, Any]:
    fmt = None
    hinted_length = _coerce_bit_length(bit_length)
    if format_data is not None:
        fmt = build_wiegand_format_from_mapping(format_data)
    else:
        fmt = get_wiegand_format(format_name, bit_length=hinted_length)
    effective_length = hinted_length or (fmt.bit_length if fmt else None)
    raw_bits = normalize_wiegand_bits(bits=bits, hex_value=hex_value, int_value=int_value, bit_length=effective_length)

    if fmt is None:
        fmt = get_wiegand_format(format_name, bit_length=len(raw_bits))
    if fmt is None:
        raise ValueError(f"unsupported Wiegand length {len(raw_bits)}")
    if len(raw_bits) != int(fmt.bit_length):
        raise ValueError(f"bit length {len(raw_bits)} does not match format {fmt.name} ({fmt.bit_length})")

    return _decode_bits_with_format(raw_bits, fmt)
