from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from typing import Iterable


@dataclass(frozen=True)
class TimeZoneChoice:
    value: str
    label: str
    offset_seconds: int


def _fmt_offset(offset_seconds: int) -> str:
    sign = '+' if offset_seconds >= 0 else '-'
    s = abs(int(offset_seconds))
    hh = s // 3600
    mm = (s % 3600) // 60
    return f"{sign}{hh:02d}:{mm:02d}"


def _fmt_gmt(offset_seconds: int) -> str:
    # Keep legacy wording users expect: GMT+2, GMT-5, also allow :30
    sign = '+' if offset_seconds >= 0 else '-'
    s = abs(int(offset_seconds))
    hh = s // 3600
    mm = (s % 3600) // 60
    if mm:
        return f"GMT{sign}{hh}:{mm:02d}"
    return f"GMT{sign}{hh}"


@lru_cache(maxsize=1)
def _load_tzdata_country_maps() -> tuple[dict[str, str], dict[str, list[str]]]:
    """Return (iso_code->country_name, tz_name->country_codes).

    Uses tzdata package files if available.
    """
    iso_names: dict[str, str] = {}
    tz_countries: dict[str, list[str]] = {}

    try:
        import tzdata  # type: ignore
        from pathlib import Path

        base = Path(tzdata.__file__).resolve().parent / 'zoneinfo'
        iso_file = base / 'iso3166.tab'
        zone_file = base / 'zone1970.tab'

        if iso_file.exists():
            for raw in iso_file.read_text(encoding='utf-8', errors='ignore').splitlines():
                line = raw.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('\t')
                if len(parts) >= 2:
                    iso_names[parts[0].strip()] = parts[1].strip()

        if zone_file.exists():
            for raw in zone_file.read_text(encoding='utf-8', errors='ignore').splitlines():
                line = raw.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('\t')
                if len(parts) < 3:
                    continue
                cc = parts[0].strip()
                tz = parts[2].strip()
                if not tz:
                    continue
                codes = [c.strip() for c in cc.split(',') if c.strip()]
                if codes:
                    tz_countries.setdefault(tz, [])
                    # Preserve order, de-dupe
                    for c in codes:
                        if c not in tz_countries[tz]:
                            tz_countries[tz].append(c)

    except Exception:
        # Best effort only.
        pass

    return iso_names, tz_countries


def _country_label_for_tz(tz_name: str, *, max_items: int = 4) -> str:
    iso_names, tz_countries = _load_tzdata_country_maps()
    codes = tz_countries.get(tz_name) or []
    if not codes:
        return ''
    names: list[str] = []
    for c in codes:
        nm = iso_names.get(c)
        if nm:
            names.append(nm)
    if not names:
        return ''
    shown = names[:max_items]
    suffix = ''
    if len(names) > max_items:
        suffix = f" +{len(names) - max_items}"
    return ', '.join(shown) + suffix


def build_time_zone_choices(zone_names: Iterable[str] | None = None) -> list[TimeZoneChoice]:
    """Build rich labels: UTC offset + GMT + tz name + countries."""
    try:
        from zoneinfo import ZoneInfo, available_timezones

        zones = sorted(zone_names) if zone_names is not None else sorted(available_timezones())
    except Exception:
        zones = ['Europe/Bucharest', 'UTC', 'Etc/UTC', 'Etc/GMT-2', 'Etc/GMT+2']

    now_utc = datetime.now(timezone.utc)
    out: list[TimeZoneChoice] = []

    for z in zones:
        try:
            from zoneinfo import ZoneInfo

            tz = ZoneInfo(z)
            local = now_utc.astimezone(tz)
            offset_td = local.utcoffset() or timezone.utc.utcoffset(now_utc)  # type: ignore[arg-type]
            offset_seconds = int(offset_td.total_seconds()) if offset_td else 0
        except Exception:
            offset_seconds = 0

        off = _fmt_offset(offset_seconds)
        gmt = _fmt_gmt(offset_seconds)
        countries = _country_label_for_tz(z)
        if countries:
            label = f"UTC{off} ({gmt}) — {z} — {countries}"
        else:
            label = f"UTC{off} ({gmt}) — {z}"

        # Help users avoid the classic Etc/GMT sign inversion confusion.
        # Example: Etc/GMT+2 == UTC-02:00 (NOT UTC+02:00).
        if z.startswith('Etc/GMT') and ('+' in z or '-' in z):
            label = f"{label} (ATENȚIE: Etc/GMT are semnul invers)"

        out.append(TimeZoneChoice(value=z, label=label, offset_seconds=offset_seconds))

    # Sort primarily by offset then by name
    out.sort(key=lambda c: (c.offset_seconds, c.value))
    return out


def build_time_zone_choice_tuples() -> list[tuple[str, str]]:
    return [(c.value, c.label) for c in build_time_zone_choices()]


def build_device_time_zone_choice_tuples() -> list[tuple[str, str]]:
    """Device modal time zone list.

    Keep it close to the legacy ZKAccessB UI: primarily Etc/GMT offsets plus a
    couple of practical defaults.

    Notes:
    - Etc/GMT±X has inverted sign by convention; labels already warn.
    """
    zone_names: list[str] = ['Europe/Bucharest', 'UTC', 'Etc/UTC', 'Etc/GMT']

    # Legacy-style list in the old UI: Etc/GMT-12 .. Etc/GMT+12 (some builds show up to 14)
    for n in range(1, 15):
        zone_names.append(f'Etc/GMT-{n}')
    for n in range(1, 15):
        zone_names.append(f'Etc/GMT+{n}')

    # De-dupe but preserve the earlier ordering for the inputs.
    seen: set[str] = set()
    ordered: list[str] = []
    for z in zone_names:
        if z in seen:
            continue
        seen.add(z)
        ordered.append(z)

    return [(c.value, c.label) for c in build_time_zone_choices(tuple(ordered))]
