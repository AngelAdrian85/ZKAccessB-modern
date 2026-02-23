from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class SyncPersonnelLimits:
    enabled: bool
    dedupe_seconds: int
    reassert_seconds: int
    batch_size: int
    inter_batch_sleep: float
    max_per_minute: int


_CACHE: Optional[SyncPersonnelLimits] = None
_CACHE_TS: float = 0.0


def _clamp_int(v: object, default: int, *, lo: int, hi: int) -> int:
    try:
        n = int(v)  # type: ignore[arg-type]
    except Exception:
        n = default
    if n < lo:
        return lo
    if n > hi:
        return hi
    return n


def _clamp_float(v: object, default: float, *, lo: float, hi: float) -> float:
    try:
        n = float(v)  # type: ignore[arg-type]
    except Exception:
        n = default
    if n < lo:
        return lo
    if n > hi:
        return hi
    return n


def _from_env() -> SyncPersonnelLimits:
    enabled = (os.getenv('SYNC_PERSONNEL_ENABLED', '1').strip() not in ('0', 'false', 'False', 'no', 'NO'))
    dedupe_seconds = _clamp_int(os.getenv('SYNC_PERSONNEL_DEDUPE_SECONDS', '60'), 60, lo=5, hi=600)
    reassert_seconds = _clamp_int(os.getenv('SYNC_PERSONNEL_REASSERT_SECONDS', '21600'), 21600, lo=60, hi=7 * 24 * 3600)
    batch_size = _clamp_int(os.getenv('SYNC_PERSONNEL_BATCH_SIZE', '200'), 200, lo=20, hi=2000)
    inter_batch_sleep = _clamp_float(os.getenv('SYNC_PERSONNEL_INTER_BATCH_SLEEP', '0.02'), 0.02, lo=0.0, hi=0.25)
    max_per_minute = _clamp_int(os.getenv('SYNC_PERSONNEL_MAX_PER_MINUTE', '0'), 0, lo=0, hi=600)
    return SyncPersonnelLimits(
        enabled=bool(enabled),
        dedupe_seconds=dedupe_seconds,
        reassert_seconds=reassert_seconds,
        batch_size=batch_size,
        inter_batch_sleep=inter_batch_sleep,
        max_per_minute=max_per_minute,
    )


def _read_from_db() -> Optional[SyncPersonnelLimits]:
    try:
        from agent.models import SystemSettings

        ss = SystemSettings.get_solo()
        enabled = bool(getattr(ss, 'sync_personnel_enabled', True))
        dedupe_seconds = _clamp_int(getattr(ss, 'sync_personnel_dedupe_seconds', 60), 60, lo=5, hi=600)
        reassert_seconds = _clamp_int(getattr(ss, 'sync_personnel_reassert_seconds', 21600), 21600, lo=60, hi=7 * 24 * 3600)
        batch_size = _clamp_int(getattr(ss, 'sync_personnel_batch_size', 200), 200, lo=20, hi=2000)
        inter_batch_sleep = _clamp_float(getattr(ss, 'sync_personnel_inter_batch_sleep', 0.02), 0.02, lo=0.0, hi=0.25)
        max_per_minute = _clamp_int(getattr(ss, 'sync_personnel_max_per_minute', 0), 0, lo=0, hi=600)
        return SyncPersonnelLimits(
            enabled=enabled,
            dedupe_seconds=dedupe_seconds,
            reassert_seconds=reassert_seconds,
            batch_size=batch_size,
            inter_batch_sleep=inter_batch_sleep,
            max_per_minute=max_per_minute,
        )
    except Exception:
        return None


def get_sync_personnel_limits(*, cache_seconds: float = 5.0, force_refresh: bool = False) -> SyncPersonnelLimits:
    """Return effective SYNC_PERSONNEL limits.

    Prefers DB (SystemSettings singleton), falls back to environment.
    Uses a short in-process cache to avoid repeated DB hits from signals.

    Note: `enabled` is intended to control *event-driven auto-enqueue* (signals).
    CommCenter still executes SYNC_PERSONNEL if a command is explicitly queued.
    """
    global _CACHE, _CACHE_TS

    now = time.time()
    if not force_refresh and _CACHE is not None and (now - _CACHE_TS) <= float(cache_seconds or 0.0):
        return _CACHE

    limits = _read_from_db() or _from_env()
    _CACHE = limits
    _CACHE_TS = now
    return limits
