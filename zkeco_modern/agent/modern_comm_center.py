"""Modernized CommCenter Agent.

This module provides a lean, maintainable version of the legacy
`dev_comm_center` process without relying on the original large
monolithic runtime. It focuses on:

1. Device session lifecycle (connect / disconnect / poll rtlog / download new logs)
2. Command queue processing (abstracted – pluggable backend)
3. Config access (DB Device rows + appconfig.ini + Django settings)
4. Health / heartbeat tracking (in-memory dict or Redis if available)

The goal is to allow incremental migration: keep legacy DB schema and
device records, but replace the Windows service with a pure Python
process started via a Django management command.

Usage:
    from agent.modern_comm_center import ModernCommCenter
    ModernCommCenter().run_forever()

This implementation deliberately avoids deep hardware operations; it
expects a backend comm driver implementing the minimal interface used
in the legacy code (connect, disconnect, get_transaction, get_rtlog, etc.).
You can drop in a real driver later or wrap existing DLL / SDK calls.
"""

from __future__ import annotations

import os
import time
import logging
import threading
import configparser
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Tuple, Callable
from collections import deque

from django.conf import settings
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.db.models import Q, Case, When, Value, IntegerField
from django.apps import apps
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .event_codes import describe as describe_event_code
from .event_codes import describe_door_event_type, describe_verify_mode

try:  # Redis optional
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None

# Prefer the current app Device model; fallback to legacy_models if present
Device = None
try:
    from agent.models import Device as DeviceModel  # type: ignore
    Device = DeviceModel
except Exception:
    try:
        from legacy_models.models import Device as LegacyDevice  # type: ignore
        Device = LegacyDevice
    except Exception:
        Device = None

LOG = logging.getLogger("modern_comm_center")

# Used by agent.views for start/stop/status endpoints.
ACTIVE_CENTER: Optional["ModernCommCenter"] = None


class CommDriver(Protocol):
    """Minimal protocol the legacy TDevComm implemented.

    Only methods observed in decompiled legacy code are declared.
    """

    def connect(self) -> Dict[str, Any]: ...
    def disconnect(self) -> Dict[str, Any]: ...
    def get_transaction(self, newlog: bool = False) -> Dict[str, Any]: ...
    def get_rtlog(self) -> Dict[str, Any]: ...
    def query_data(self, table: str, fields: str, flt: str, extra: str) -> Dict[str, Any]: ...
    def update_data(self, table: str, data: str, extra: str) -> Dict[str, Any]: ...
    def delete_data(self, table: str, flt: str) -> Dict[str, Any]: ...
    def Get_Data_Count(self, table: str) -> Dict[str, Any]: ...
    def controldevice(self, door: int, index: int, state: int) -> Dict[str, Any]: ...
    def control_normal_open(self, door: int, state: int) -> Dict[str, Any]: ...
    def cancel_alarm(self, door: str) -> Dict[str, Any]: ...
    def get_options(self, items: str) -> Dict[str, Any]: ...
    def set_options(self, items: str) -> Dict[str, Any]: ...


@dataclass
class DeviceSession:
    device_id: int
    sn: str
    name: str
    driver: CommDriver
    last_connect_ts: float = 0.0
    connected: bool = False
    fails: int = 0
    rtlog_fail_threshold: int = 5
    reconnect_backoff_s: float = 1.0
    next_connect_ts: float = 0.0
    config: Dict[str, Any] = field(default_factory=dict)
    last_adms_autoconfig_ts: float = 0.0
    last_adms_items: str = ''
    last_tx_poll_ts: float = 0.0

    def connect(self) -> bool:
        try:
            now_ts = time.time()
            if self.next_connect_ts and now_ts < float(self.next_connect_ts):
                return False
        except Exception:
            pass
        ret = self.driver.connect()
        ok = ret.get("result", -1) >= 0 or ret.get("hcommpro", 0) > 0
        self.connected = ok
        self.last_connect_ts = time.time()
        if ok:
            self.reconnect_backoff_s = 1.0
            self.next_connect_ts = 0.0
        else:
            try:
                self.reconnect_backoff_s = min(30.0, max(1.0, float(self.reconnect_backoff_s) * 2.0))
            except Exception:
                self.reconnect_backoff_s = 5.0
            try:
                self.next_connect_ts = time.time() + float(self.reconnect_backoff_s)
            except Exception:
                self.next_connect_ts = 0.0
        try:
            if ok:
                LOG.debug("connect device=%s result=%s", self.sn, ret)
            else:
                LOG.warning(
                    "connect failed device=%s result=%s error=%s",
                    self.sn,
                    ret.get('result'),
                    (ret.get('error') or ret.get('data') or ''),
                )
        except Exception:
            pass
        return ok

    def disconnect(self) -> None:
        try:
            self.driver.disconnect()
        finally:
            self.connected = False
            LOG.debug("disconnect device=%s", self.sn)

    def poll_rtlog(self) -> List[str]:
        if not self.connected:
            return []
        ret = self.driver.get_rtlog()
        if ret.get("result", -1) < 0:
            self.fails += 1
            try:
                LOG.warning(
                    "rtlog fail device=%s result=%s error=%s",
                    self.sn,
                    ret.get('result'),
                    (ret.get('error') or ret.get('data') or ''),
                )
            except Exception:
                LOG.warning("rtlog fail device=%s result=%s", self.sn, ret.get("result"))
            if self.fails >= self.rtlog_fail_threshold:
                self.disconnect()
            return []
        self.fails = 0
        data = ret.get("data") or ""
        if isinstance(data, basestring if 'basestring' in globals() else str):  # py2/py3 compat
            return [d for d in data.split("\r\n") if d]
        return []

    def down_new_logs(self) -> List[str]:
        if not self.connected:
            return []
        ret = self.driver.get_transaction(newlog=True)
        if ret.get("result", -1) <= 0:
            return []
        data = ret.get("data", {})
        logs = []
        # legacy format: data indexed from 1..N
        for i in range(1, ret.get("result", 0) + 1):
            line = data.get(i)
            if line:
                logs.append(line)
        return logs


class InMemoryQueue(object):
    """Simple in-memory queue placeholder for command processing."""
    def __init__(self):
        self._q: List[Tuple[int, str]] = []
        self._lock = threading.Lock()

    def push(self, device_id: int, cmd: str) -> None:
        with self._lock:
            self._q.append((device_id, cmd))

    def pop(self) -> Optional[Tuple[int, str]]:
        with self._lock:
            if not self._q:
                return None
            return self._q.pop(0)


class RedisQueue(object):
    """Redis-backed queue implementation using LPUSH / RPOP."""
    def __init__(self, client: 'redis.Redis', key: str = 'commcenter:cmdq'):
        self.client = client
        self.key = key

    def push(self, device_id: int, cmd: str) -> None:
        payload = f"{device_id}:{cmd}"
        self.client.lpush(self.key, payload)

    def pop(self) -> Optional[Tuple[int, str]]:
        data = self.client.rpop(self.key)
        if not data:
            return None
        raw = data.decode() if isinstance(data, bytes) else data
        if ':' not in raw:
            return None
        dev_str, cmd = raw.split(':', 1)
        try:
            return int(dev_str), cmd
        except ValueError:  # pragma: no cover
            return None


class HeartbeatBackend(Protocol):
    def set(self, field: str, value: Any) -> None: ...
    def get(self, field: str) -> Any: ...


class InMemoryHeartbeat(object):
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def set(self, field: str, value: Any) -> None:
        with self._lock:
            self._data[field] = value

    def get(self, field: str) -> Any:
        with self._lock:
            return self._data.get(field)


class RedisHeartbeat(object):
    def __init__(self, client: 'redis.Redis', key: str = 'commcenter:heartbeat'):
        self.client = client
        self.key = key

    def set(self, field: str, value: Any) -> None:
        self.client.hset(self.key, field, value)

    def get(self, field: str) -> Any:
        val = self.client.hget(self.key, field)
        if isinstance(val, bytes):
            try:
                return val.decode()
            except Exception:  # pragma: no cover
                return val
        return val


class ModernCommCenter(object):
    """Coordinator for DeviceSession objects.

    Responsibilities:
    - Load configuration (DB + appconfig.ini)
    - Build device sessions with injected drivers (currently stubbed)
    - Process command queue
    - Periodic rtlog polling & new log downloads
    - Heartbeat tracking
    """

    def __init__(self,
                 poll_interval: float = 1.0,
                 download_hours: Optional[List[int]] = None,
                 queue_backend: Optional[Any] = None,
                 heartbeat_backend: Optional[HeartbeatBackend] = None):
        self.poll_interval = poll_interval
        self.download_hours = download_hours or []
        self.sessions: Dict[int, DeviceSession] = {}
        self.cmd_queue = queue_backend or InMemoryQueue()
        self._stop = threading.Event()
        self.heartbeat_backend = heartbeat_backend or InMemoryHeartbeat()
        self.app_cfg = self._load_app_config()
        # Metrics counters
        self.total_rtlog_lines = 0
        self.total_event_logs = 0
        self.cycles = 0
        # New-log download throttling (prevents hammering devices every poll cycle)
        self._last_download_ts: float = 0.0
        try:
            self.download_cooldown_s: float = float(os.getenv('COMM_DOWNLOAD_COOLDOWN', '15'))
        except Exception:
            self.download_cooldown_s = 15.0
        # Lightweight per-device rtlog de-duplication (prevents infinite repeats)

        # SYNC_PERSONNEL global rate limiter (optional)
        self._sync_personnel_exec_ts = deque()  # type: ignore[var-annotated]

        self._rtlog_last_line: Dict[int, str] = {}  # kept for legacy compat
        # Rolling per-device rtlog de-duplication (prevents ring-buffer re-reads after reconnect).
        # Key: device_id → set of seen fingerprint strings (hash of time_second+pin+door+code)
        self._rtlog_seen: Dict[int, set] = {}
        self._rtlog_seen_order: Dict[int, deque] = {}
        self.rtlog_dedupe_window: int = 2000
        # Per-device panel user-card cache: PIN → CardNo downloaded from panel's user table.
        # Refreshed on connect and every PANEL_CARD_CACHE_TTL seconds.
        self._panel_card_cache: Dict[int, Dict[str, str]] = {}
        self._panel_card_cache_ts: Dict[int, float] = {}
        # Per-device PIN→card lookup cache for UI enrichment (populated from Django DB fallback).
        self._pin_card_cache: Dict[int, Dict[str, str]] = {}
        self.panel_card_cache_ttl: float = 300.0  # refresh every 5 minutes
        # Rolling per-device event-log de-duplication (prevents repeated downloads creating duplicates)
        self._event_recent: Dict[int, set[str]] = {}
        self._event_recent_order: Dict[int, deque[str]] = {}
        self.event_dedupe_window: int = 500
        self.state_store = None
        try:
            from .state import DeviceStateStore
            self.state_store = DeviceStateStore(os.getenv('REDIS_URL'))
        except Exception:  # pragma: no cover
            self.state_store = None
        self._channel_layer = None
        try:
            self._channel_layer = get_channel_layer()
        except Exception:  # pragma: no cover
            self._channel_layer = None

        # Persisted heartbeat / last-seen tracking.
        # DeviceStatus.updated_at is treated as a state-change timestamp in many places;
        # use Device.last_contact as the liveness/heartbeat timestamp.
        self._last_contact_persist_ts: Dict[int, float] = {}
        try:
            self.last_contact_interval_s: float = float(os.getenv('COMM_LAST_CONTACT_INTERVAL', '30'))
        except Exception:
            self.last_contact_interval_s = 30.0

    def _get_sync_limits(self):
        try:
            from agent.sync_limits import get_sync_personnel_limits

            return get_sync_personnel_limits()
        except Exception:
            return None

    def _sync_personnel_rate_peek_ok(self) -> bool:
        """Return True if we are allowed to start another SYNC_PERSONNEL now (global)."""
        limits = self._get_sync_limits()
        try:
            max_per_min = int(getattr(limits, 'max_per_minute', 0) or 0) if limits is not None else 0
        except Exception:
            max_per_min = 0
        if max_per_min <= 0:
            return True

        now = time.time()
        cutoff = now - 60.0
        try:
            while self._sync_personnel_exec_ts and float(self._sync_personnel_exec_ts[0]) < cutoff:
                self._sync_personnel_exec_ts.popleft()
        except Exception:
            self._sync_personnel_exec_ts = deque()
        try:
            return len(self._sync_personnel_exec_ts) < max_per_min
        except Exception:
            return True

    def _sync_personnel_rate_record(self) -> None:
        try:
            self._sync_personnel_exec_ts.append(time.time())
        except Exception:
            pass

    def _touch_last_contact(self, device_id: int) -> Optional[str]:
        """Persist a throttled liveness timestamp and broadcast it.

        Returns the ISO timestamp broadcast (or None if skipped).
        """
        try:
            now_ts = time.time()
            last = float(self._last_contact_persist_ts.get(int(device_id), 0.0) or 0.0)
            if self.last_contact_interval_s > 0 and (now_ts - last) < self.last_contact_interval_s:
                return None
            self._last_contact_persist_ts[int(device_id)] = now_ts

            now = timezone.now()
            try:
                DeviceModel = apps.get_model('agent', 'Device')
            except Exception:
                DeviceModel = Device
            if not DeviceModel:
                return None
            if not hasattr(DeviceModel, 'last_contact'):
                return None
            try:
                DeviceModel.objects.filter(pk=int(device_id)).update(last_contact=now)
            except Exception:
                return None

            iso = now.isoformat() if hasattr(now, 'isoformat') else str(now)
            try:
                from agent.ws import broadcast_device_status
                broadcast_device_status(int(device_id), True, updated_at=iso)
            except Exception:
                pass

            # Keep runtime last-broadcast timestamps in sync for new WebSocket clients.
            try:
                import json
                base = getattr(settings, 'BASE_DIR', os.getcwd())
                rt_dir = os.path.join(base, 'zkeco_modern', 'runtime_logs')
                os.makedirs(rt_dir, exist_ok=True)
                rt_file = os.path.join(rt_dir, 'last_status_broadcasts.json')
                data = {}
                if os.path.exists(rt_file):
                    try:
                        with open(rt_file, 'r', encoding='utf-8') as fh:
                            data = json.load(fh) or {}
                    except Exception:
                        data = {}
                data[str(int(device_id))] = iso
                try:
                    with open(rt_file, 'w', encoding='utf-8') as fh:
                        json.dump(data, fh)
                except Exception:
                    pass
            except Exception:
                pass
            return iso
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    def _load_app_config(self) -> Dict[str, Any]:
        path = os.path.join(settings.BASE_DIR if hasattr(settings, "BASE_DIR") else os.getcwd(), "appconfig.ini")
        cfg = {}
        if os.path.exists(path):
            parser = configparser.ConfigParser()
            try:
                parser.read(path)
                if parser.has_section("iaccess"):
                    cfg = {k: parser.get("iaccess", k) for k in parser.options("iaccess")}
            except Exception as e:  # pragma: no cover
                LOG.warning("Failed reading appconfig.ini: %s", e)
        return cfg

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------
    def build_sessions(self, driver_factory) -> None:
        if Device is None:
            LOG.error("Device model unavailable.")
            return
        for dev in Device.objects.all():  # type: ignore[attr-defined]
            try:
                driver = driver_factory(dev)
                session = DeviceSession(
                    device_id=dev.id,
                    sn=(getattr(dev, 'serial_number', None) or getattr(dev, 'sn', None) or ''),
                    name=(getattr(dev, 'name', None) or getattr(dev, 'device_name', None) or ''),
                    driver=driver,
                    config={
                        "com_address": getattr(dev, "com_address", None),
                        "com_port": getattr(dev, "com_port", None),
                        "ip_address": getattr(dev, "ip_address", None),
                        "ip_port": getattr(dev, "port", None),
                    },
                )
                self.sessions[dev.id] = session
            except Exception as e:  # pragma: no cover
                LOG.error("Failed to init session for device %s: %s", dev.id, e)

    def _maybe_autoconfig_adms_push(self, session: DeviceSession) -> None:
        """Best-effort auto-configure ADMS/iClock push on a connected session.

        Controlled via env vars:
          - ZKACCESS_ADMS_AUTOCONFIG: default '1' (0/false/no/off disables)
          - ZKACCESS_ADMS_ADDR: optional explicit server IP
          - ZKACCESS_ADMS_PORT: required server port (tray_agent sets this)
        """
        try:
            flag = str(os.getenv('ZKACCESS_ADMS_AUTOCONFIG', '1') or '').strip().lower()
            if flag in ('0', 'false', 'no', 'off'):
                return
        except Exception:
            return

        # Port must be known (which web server port devices can reach).
        try:
            port_raw = str(os.getenv('ZKACCESS_ADMS_PORT', '') or '').strip()
            if not port_raw:
                return
            port_int = int(port_raw)
            if port_int <= 0 or port_int > 65535:
                return
        except Exception:
            return

        server_addr = str(os.getenv('ZKACCESS_ADMS_ADDR', '') or '').strip()
        if not server_addr:
            dev_ip = ''
            try:
                dev_ip = str((session.config or {}).get('ip_address') or '').strip()
            except Exception:
                dev_ip = ''
            if dev_ip:
                try:
                    import socket as _socket
                    s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
                    s.connect((dev_ip, 1))
                    server_addr = str(s.getsockname()[0] or '').strip()
                    s.close()
                except Exception:
                    server_addr = ''

        if not server_addr or server_addr.startswith('127.'):
            return

        # Many firmwares will accept ServerAddr/ServerPort but still not start pushing
        # transactions unless realtime flags are enabled.
        items = (
            f"ServerAddr={server_addr},ServerPort={int(port_int)},"
            f"CLOUDSERVICEFLAG=1,ADMSServerIP={server_addr},"
            f"WebServerURL=http://{server_addr}:{int(port_int)},"
            f"TransFlag=1,Realtime=1,RTLog=1,TransInterval=1"
        )
        now_ts = time.time()
        try:
            if session.last_adms_items == items and (now_ts - float(session.last_adms_autoconfig_ts or 0.0)) < 600.0:
                return
        except Exception:
            pass

        try:
            ret = session.driver.set_options(items)
            if isinstance(ret, dict):
                try:
                    ok = int(ret.get('result', -1)) >= 0
                except Exception:
                    ok = bool(ret.get('result'))
            else:
                ok = bool(ret)
        except Exception as e:
            LOG.debug('ADMS autoconfig exception device=%s: %s', session.sn, e)
            return

        if ok:
            session.last_adms_items = items
            session.last_adms_autoconfig_ts = now_ts
            LOG.info('ADMS autoconfig device=%s addr=%s port=%s ok', session.sn, server_addr, port_int)
            try:
                AuditLog = apps.get_model('agent', 'AuditLog')
                AuditLog.objects.create(
                    module='device',
                    action='adms_autoconfig',
                    entity_id=int(session.device_id),
                    entity_name=str(session.sn or session.name or ''),
                    details=f"ServerAddr={server_addr} ServerPort={int(port_int)}",
                )
            except Exception:
                pass
        else:
            LOG.warning('ADMS autoconfig device=%s failed ret=%s', session.sn, ret)

    def connect_all(self) -> None:
        enabled_ids = None
        try:
            if Device is not None:
                enabled_ids = set(Device.objects.filter(enabled=True).values_list('id', flat=True))  # type: ignore[attr-defined]
        except Exception:
            enabled_ids = None

        for session in self.sessions.values():
            if enabled_ids is not None and int(session.device_id) not in enabled_ids:
                if session.connected:
                    try:
                        session.disconnect()
                    except Exception:
                        pass
                continue
            if not session.connected:
                if session.connect():
                    try:
                        self._maybe_autoconfig_adms_push(session)
                    except Exception:
                        pass
                    if self.state_store:
                        self.state_store.update_device(session.device_id, online=True)
                    # Persist authoritative DeviceStatus and broadcast its updated_at
                    ua = None
                    # Probe for real device activity (rtlog) before deciding to persist
                    # a change in the DB. This prevents marking devices 'online' at
                    # CommCenter start purely because the driver returned a connect
                    # success; instead we require evidence (rtlog) that the device
                    # is responsive.
                    try:
                        probe_lines = session.poll_rtlog()
                    except Exception:
                        probe_lines = []

                    # Download panel user→card mapping so rtlog PIN enrichment uses
                    # the actual Wiegand card number stored on the panel.
                    self._refresh_panel_card_cache(session)

                    # Auto time-sync: set device clock to local server time on connect.
                    # This corrects ZKTeco panel clock drift without requiring manual action.
                    try:
                        dev_obj = None
                        try:
                            _DevModel = apps.get_model('agent', 'Device')
                            dev_obj = _DevModel.objects.filter(pk=session.device_id).first()
                        except Exception:
                            pass
                        if dev_obj is None or getattr(dev_obj, 'auto_sync_time', True):
                            from datetime import datetime as _dt
                            _ts_local = _dt.now().strftime('%Y-%m-%d %H:%M:%S')
                            session.driver.set_options(f'DateTimeStr={_ts_local}')
                            LOG.info('Auto time sync device=%s ts=%s', session.sn, _ts_local)
                    except Exception as _e:
                        LOG.debug('Auto time sync failed device=%s: %s', session.sn, _e)

                    # NOTE: poll_rtlog() consumes RTLOG lines from the device.
                    # When used as a connectivity probe, we must persist/broadcast
                    # any lines retrieved here; otherwise real card scans can be
                    # dropped during (re)connect.
                    try:
                        if probe_lines:
                            filtered = self._persist_rtlog(session, probe_lines)
                            if filtered:
                                self.total_rtlog_lines += len(filtered)
                                self._touch_last_contact(session.device_id)
                                if self.state_store:
                                    self.state_store.update_device(session.device_id, online=True)
                                self._publish_event({"type": "rtlog.batch", "device_id": session.device_id, "lines": filtered})
                    except Exception:
                        pass
                    try:
                        # Use apps.get_model to avoid module import/app registry inconsistencies
                        DeviceStatus = apps.get_model('agent', 'DeviceStatus')
                        # Update or create status row for this device
                        try:
                            with transaction.atomic():
                                # Do NOT create DeviceStatus rows on commcenter startup. Creating here
                                # records the commcenter/server start time in `updated_at`, which can
                                # be mistaken for a real device state-change. Only update existing
                                # status rows and skip creation.
                                obj = DeviceStatus.objects.filter(device_id=session.device_id).first()
                                if obj:
                                    # Only persist when there's an actual state change.
                                    prev_online = bool(obj.online)
                                    changed = False
                                    # Mark device online as soon as connect() succeeds.
                                    # The previous probe_lines guard was too strict:
                                    # an idle panel produces no RTLOG data yet is fully online.
                                    if not prev_online:
                                        obj.online = True
                                        changed = True
                                    if obj.door_state != '':
                                        obj.door_state = ''
                                        changed = True
                                    if changed:
                                        # Persist updated_at on real state-change or after
                                        # the first cycle (avoids writing server start-time
                                        # on cycles=0 for unchanged devices).
                                        should_persist_updated = not prev_online or getattr(self, 'cycles', 0) > 0
                                        if should_persist_updated:
                                            obj.save(update_fields=['online', 'door_state', 'updated_at'])
                                        else:
                                            obj.save(update_fields=['online', 'door_state'])
                                    try:
                                        ua = getattr(obj, 'updated_at', None)
                                        if ua is not None:
                                            ua = ua.isoformat() if hasattr(ua, 'isoformat') else str(ua)
                                    except Exception:
                                        ua = None
                                else:
                                    # No prior status known for this device; skip creating a new row
                                    ua = None
                        except IntegrityError as e:
                            LOG.warning('DeviceStatus persist IntegrityError device=%s: %s', session.device_id, e)
                        except Exception as e:
                            LOG.warning('DeviceStatus persist failed device=%s: %s', session.device_id, e)
                    except Exception:
                        # apps.get_model may fail in weird import states; fall back to local timestamp
                        ua = None

                    # For the initial startup broadcast we want clients to show a fresh 'last seen'
                    # timestamp so the dashboard UI updates immediately. Use the current time for
                    # the broadcast, but do NOT persist this value to the DB unless a real
                    # device state change occurred (handled above by obj.save()).
                    # Prefer the persisted DB timestamp when present; only fall back to
                    # current time for devices without any persisted `DeviceStatus`.
                    if ua:
                        ua_broadcast = ua
                    else:
                        try:
                            ua_broadcast = timezone.now().isoformat()
                        except Exception:
                            ua_broadcast = None

                    try:
                        from agent.ws import broadcast_device_status
                        broadcast_device_status(session.device_id, True, serial=session.sn, updated_at=ua_broadcast)
                        # Persist last broadcast timestamp to runtime file so WebSocket consumers
                        # can show the most-recent 'last seen' value even if DB wasn't written.
                        try:
                            import json, os
                            base = getattr(settings, 'BASE_DIR', os.getcwd())
                            rt_dir = os.path.join(base, 'zkeco_modern', 'runtime_logs')
                            os.makedirs(rt_dir, exist_ok=True)
                            rt_file = os.path.join(rt_dir, 'last_status_broadcasts.json')
                            data = {}
                            if os.path.exists(rt_file):
                                try:
                                    with open(rt_file, 'r', encoding='utf-8') as fh:
                                        data = json.load(fh) or {}
                                except Exception:
                                    data = {}
                            data[str(session.device_id)] = ua_broadcast
                            try:
                                with open(rt_file, 'w', encoding='utf-8') as fh:
                                    json.dump(data, fh)
                            except Exception:
                                pass
                        except Exception:
                            pass
                    except Exception as e:
                        try:
                            LOG.warning('broadcast_device_status import/call failed: %s', e)
                        except Exception:
                            pass
                        try:
                            print('broadcast_device_status import/call failed:', e, flush=True)
                        except Exception:
                            pass
                        # Fallback: publish simple device.online event (include updated_at if available)
                        payload = {"type": "device.online", "device_id": session.device_id, "sn": session.sn}
                        if ua:
                            payload["updated_at"] = ua
                        self._publish_event(payload)

    # ------------------------------------------------------------------
    # Command handling
    # ------------------------------------------------------------------
    def enqueue_command(self, device_id: int, cmd: str) -> None:
        self.cmd_queue.push(device_id, cmd)

    def _pop_pending_command_from_db(self) -> Optional[tuple[int, int, str]]:
        """Pop one pending command from DB.

        This enables command execution even when the web process isn't sharing
        the in-memory queue with CommCenter (separate processes).

        Safety: only an allow-list of command prefixes are executed.
        """
        try:
            CommandLog = apps.get_model('agent', 'CommandLog')
        except Exception:
            return None

        try:
            # Prefer connected devices, but also allow disconnected devices whose
            # reconnect backoff window has elapsed. Otherwise, commands can get
            # stuck forever when a device is flapping (connects briefly, then
            # disconnects before the command pop window).
            now_ts = time.time()
            eligible_ids: list[int] = []
            for s in self.sessions.values():
                try:
                    dev_id = int(getattr(s, 'device_id', 0) or 0)
                except Exception:
                    dev_id = 0
                if dev_id <= 0:
                    continue
                try:
                    if getattr(s, 'connected', False):
                        eligible_ids.append(dev_id)
                        continue
                except Exception:
                    pass
                try:
                    next_ts = float(getattr(s, 'next_connect_ts', 0.0) or 0.0)
                except Exception:
                    next_ts = 0.0
                if now_ts >= next_ts:
                    eligible_ids.append(dev_id)

            if not eligible_ids:
                return None

            allow_prefixes = (
                'SYNC_ALL',
                'SYNC_PERSONNEL',
                'SYNC_ACCESS_LEVELS',
                'SYNC_TIME',
                'REAL_LOG',
                'DOWN_NEWLOG',
                'CONNECT',
                'DISCONNECT',
                'CLEAR_DEVICE_DATA',
                'DOOR_',
                'REBOOT',
                'SET_OPTION',
                'GET_OPTION',
            )

            with transaction.atomic():
                row = (
                    CommandLog.objects
                    .select_for_update(skip_locked=True)
                    .filter(device_id__in=eligible_ids)
                    .filter(
                        Q(status='PENDING')
                        | Q(status='RUNNING', executed_at__isnull=True, result__startswith='queued')
                    )
                    .annotate(
                        _conn_prio=Case(
                            When(device_id__in=[int(s.device_id) for s in self.sessions.values() if getattr(s, 'connected', False)], then=Value(0)),
                            default=Value(1),
                            output_field=IntegerField(),
                        ),
                        _door_prio=Case(
                            When(command__startswith='DOOR_', then=Value(0)),
                            When(command__startswith='REBOOT', then=Value(1)),
                            When(command__startswith='GET_OPTION', then=Value(1)),
                            default=Value(2),
                            output_field=IntegerField(),
                        )
                    )
                    .order_by('_conn_prio', '_door_prio', 'created_at')
                    .first()
                )
                if not row:
                    return None

                try:
                    cmdtxt = str(getattr(row, 'command', '') or '')
                except Exception:
                    cmdtxt = ''
                if not cmdtxt or not cmdtxt.startswith(allow_prefixes):
                    try:
                        CommandLog.objects.filter(id=int(row.id), status='PENDING').update(status='ERR', result='unsupported')
                    except Exception:
                        pass
                    return None

                # Global rate limit (hard cap) for heavy sync commands.
                if cmdtxt.startswith(('SYNC_ALL', 'SYNC_PERSONNEL', 'SYNC_ACCESS_LEVELS')) and (not self._sync_personnel_rate_peek_ok()):
                    return None

                updated = (
                    CommandLog.objects
                    .filter(
                        id=int(row.id),
                        status__in=('PENDING', 'RUNNING'),
                        executed_at__isnull=True,
                    )
                    .update(status='RUNNING')
                )
                if updated != 1:
                    return None
                return (int(row.id), int(row.device_id or 0), cmdtxt)
        except Exception:
            return None

    def _mark_command_log(self, cmdlog_id: int, *, status: str, result: str = "") -> None:
        try:
            CommandLog = apps.get_model('agent', 'CommandLog')
            obj = CommandLog.objects.filter(id=int(cmdlog_id)).first()
            if not obj:
                return
            obj.status = (status or 'OK')[:16]
            obj.result = (result or '')[:128]
            obj.executed_at = timezone.now()
            obj.save(update_fields=['status', 'result', 'executed_at'])
            try:
                from agent.views import _broadcast_command  # type: ignore
                _broadcast_command(obj)
            except Exception:
                pass
        except Exception:
            pass

    def _sync_personnel_to_device(self, session: DeviceSession) -> tuple[bool, str]:
        """Push server personnel/department/access rights to the controller.

        Writes device tables:
        - timezone (derived from TimeSegment)
        - user
        - userauthorize
        """
        try:
            Door = apps.get_model('agent', 'Door')
            Employee = apps.get_model('agent', 'Employee')
            AccessLevel = apps.get_model('agent', 'AccessLevel')
            TimeSegment = apps.get_model('agent', 'TimeSegment')
        except Exception as e:
            return (False, f"models_unavailable:{e}")

        # Throttling / no-op behavior
        limits = self._get_sync_limits()

        try:
            reassert_s = int(getattr(limits, 'reassert_seconds', 21600)) if limits is not None else 21600
        except Exception:
            reassert_s = 21600
        reassert_s = max(60, min(7 * 24 * 3600, int(reassert_s)))

        try:
            batch_size = int(getattr(limits, 'batch_size', 200)) if limits is not None else 200
        except Exception:
            batch_size = 200
        batch_size = max(20, min(2000, int(batch_size)))

        try:
            inter_sleep = float(getattr(limits, 'inter_batch_sleep', 0.02)) if limits is not None else 0.02
        except Exception:
            inter_sleep = 0.02
        inter_sleep = max(0.0, min(0.25, float(inter_sleep)))

        def _pack_time(st, en) -> int:
            stv = int(getattr(st, 'hour', 0)) * 100 + int(getattr(st, 'minute', 0))
            env = int(getattr(en, 'hour', 0)) * 100 + int(getattr(en, 'minute', 0))
            return int((stv << 16) + (env & 0xFFFF))

        def _line_kv(items: list[tuple[str, object]]) -> str:
            parts: list[str] = []
            for k, v in items:
                if v is None:
                    continue
                parts.append(f"{k}={v}")
            return "\t".join(parts)

        def _default_dt_range(emp) -> tuple[str, str]:
            try:
                sd = getattr(emp, 'acc_startdate', None)
                ed = getattr(emp, 'acc_enddate', None)
                if sd:
                    st = f"{sd:%Y-%m-%d} 00:00:00"
                else:
                    st = "2000-01-01 00:00:00"
                if ed:
                    et = f"{ed:%Y-%m-%d} 23:59:59"
                else:
                    et = "2099-12-31 23:59:59"
                return st, et
            except Exception:
                return ("2000-01-01 00:00:00", "2099-12-31 23:59:59")

        def _pick_pin(emp) -> int:
            try:
                v = getattr(emp, 'legacy_userid', None)
                if v is not None and str(v).strip() != '':
                    return int(v)
            except Exception:
                pass
            return int(getattr(emp, 'id'))

        def _normalize_cardno(raw: str) -> str | None:
            """Return a numeric CardNo string suitable for controller user table.

            Many ZKTeco panels expect CardNo to be a decimal integer (often 32-bit).
            Our DB may store reader output as hex (e.g. '01131A533A').
            """
            try:
                s = (raw or '').strip()
                if not s:
                    return None
                if s.isdigit():
                    return s
                import re

                if re.fullmatch(r"[0-9a-fA-F]+", s or ''):
                    v = int(s, 16)
                    # Panels commonly store card numbers as unsigned 32-bit.
                    if v < 0:
                        return None
                    if v > 0xFFFFFFFF:
                        v = v & 0xFFFFFFFF
                    if v == 0:
                        return None
                    return str(v)
                return None
            except Exception:
                return None

        doors = list(Door.objects.filter(device_id=int(session.device_id)).exclude(door_number__isnull=True))
        door_numbers = sorted({int(getattr(d, 'door_number') or 0) for d in doors if int(getattr(d, 'door_number') or 0) > 0})
        if not door_numbers:
            return (False, "no_doors_configured")

        levels = list(AccessLevel.objects.filter(doors__in=doors).distinct())
        if not levels:
            # Starting-from-scratch mode: if there are no access levels yet, do not fail.
            # This is a safe no-op; controllers will deny access by default.
            return (True, "no_access_levels_for_device")

        employees = (
            Employee.objects.filter(active=True, access_levels__in=levels)
            .distinct()
            .prefetch_related('access_levels', 'access_levels__doors', 'access_levels__time_segments')
        )

        user_lines: list[str] = []
        ua_lines: list[str] = []
        tz_ids: set[int] = set()
        verify_warnings: list[str] = []

        for emp in employees:
            pin = _pick_pin(emp)
            card_raw = (getattr(emp, 'card_number', '') or '').strip()
            card = _normalize_cardno(card_raw)
            name = (f"{getattr(emp, 'first_name', '')} {getattr(emp, 'last_name', '')}").strip()
            dept_id = getattr(emp, 'dept_id', None)
            try:
                group = int(dept_id) if dept_id is not None else 1
            except Exception:
                group = 1

            st, et = _default_dt_range(emp)
            pw = (getattr(emp, 'password_on_record', '') or '').strip()
            super_auth = 1 if bool(getattr(emp, 'access_superuser', False)) else 0

            user_lines.append(
                _line_kv([
                    ("Pin", pin),
                    ("CardNo", card),
                    ("Name", name),
                    ("Password", pw),
                    ("Group", group),
                    ("StartTime", st),
                    ("EndTime", et),
                    ("SuperAuthorize", super_auth),
                ])
            )

            # Compute door mask + timezone from access levels on this device
            mask = 0
            tz_id = None
            try:
                # Deterministic iteration helps if multiple levels are assigned.
                for al in getattr(emp, 'access_levels').all().order_by('id'):
                    level_mask = 0

                    # doors on this device
                    for d in al.doors.all():
                        if int(getattr(d, 'device_id', 0) or 0) != int(session.device_id):
                            continue
                        dn = int(getattr(d, 'door_number', 0) or 0)
                        if dn > 0:
                            level_mask |= (1 << (dn - 1))

                    # Only levels that actually contribute doors on THIS device
                    # are allowed to influence door mask and timezone selection.
                    if not level_mask:
                        continue

                    mask |= level_mask

                    if tz_id is None:
                        seg = al.time_segments.all().order_by('id').first()
                        if seg is not None:
                            tz_id = int(getattr(seg, 'id'))
            except Exception:
                pass

            if not mask:
                continue
            if tz_id is None:
                # Conservative default: try first TimeSegment, otherwise 1
                try:
                    seg0 = TimeSegment.objects.order_by('id').first()
                    tz_id = int(getattr(seg0, 'id')) if seg0 else 1
                except Exception:
                    tz_id = 1
            tz_ids.add(int(tz_id))
            ua_lines.append(_line_kv([("Pin", pin), ("AuthorizeTimezoneId", int(tz_id)), ("AuthorizeDoorId", int(mask))]))

        if not user_lines:
            return (False, "no_employees_match_device")

        # Sync referenced time segments as device timezones
        tz_lines: list[str] = []
        try:
            for seg in TimeSegment.objects.filter(id__in=sorted(tz_ids)).order_by('id'):
                sid = int(getattr(seg, 'id'))
                st = getattr(seg, 'start_time', None)
                en = getattr(seg, 'end_time', None)
                if st is None or en is None:
                    continue
                packed = _pack_time(st, en)
                days_mask = int(getattr(seg, 'days_mask', 0) or 0)

                # Our days_mask: bit0=Mon..bit6=Sun
                def day_active(bit_idx: int) -> bool:
                    return bool(days_mask & (1 << bit_idx))

                tz_lines.append(
                    _line_kv([
                        ("TimezoneId", sid),
                        ("SunTime1", packed if day_active(6) else 0), ("SunTime2", 0), ("SunTime3", 0),
                        ("MonTime1", packed if day_active(0) else 0), ("MonTime2", 0), ("MonTime3", 0),
                        ("TueTime1", packed if day_active(1) else 0), ("TueTime2", 0), ("TueTime3", 0),
                        ("WedTime1", packed if day_active(2) else 0), ("WedTime2", 0), ("WedTime3", 0),
                        ("ThuTime1", packed if day_active(3) else 0), ("ThuTime2", 0), ("ThuTime3", 0),
                        ("FriTime1", packed if day_active(4) else 0), ("FriTime2", 0), ("FriTime3", 0),
                        ("SatTime1", packed if day_active(5) else 0), ("SatTime2", 0), ("SatTime3", 0),
                        ("Hol1Time1", 0), ("Hol1Time2", 0), ("Hol1Time3", 0),
                        ("Hol2Time1", 0), ("Hol2Time2", 0), ("Hol2Time3", 0),
                        ("Hol3Time1", 0), ("Hol3Time2", 0), ("Hol3Time3", 0),
                    ])
                )
        except Exception as e:
            return (False, f"build_timezone_failed:{e}")

        def _payload_hash() -> str:
            try:
                import hashlib

                payload = (
                    'TZ\n' + "\n".join(tz_lines) +
                    '\nUSER\n' + "\n".join(user_lines) +
                    '\nUA\n' + "\n".join(ua_lines)
                )
                return hashlib.sha256(payload.encode('utf-8', 'ignore')).hexdigest()[:16]
            except Exception:
                return ''

        def _device_has_users() -> bool | None:
            """Best-effort check whether the controller currently stores any users.

            Returns:
            - True: user table appears non-empty
            - False: user table appears empty
            - None: cannot determine (driver/table limitation)
            """
            # Prefer row-count style checks when available.
            try:
                cnt = session.driver.Get_Data_Count('user')
                c = int((cnt or {}).get('result', -1))
                if c >= 0:
                    return c > 0
            except Exception:
                pass

            # Fallback to querying the user table directly.
            try:
                q = session.driver.query_data('user', fields='Pin,CardNo', filter='', option='')
                qres = int((q or {}).get('result', -1))
                if qres < 0:
                    return None
                raw = str((q or {}).get('data') or '').replace('\x00', '')
                rows = [ln for ln in raw.split('\r\n') if str(ln or '').strip()]
                if not rows:
                    return False
                # Query output commonly includes one header line.
                for rr in rows[1:]:
                    vals = [v.strip() for v in str(rr).split(',')]
                    if any(vals):
                        return True
                return False
            except Exception:
                return None

        sig = _payload_hash()

        # If the last successful sync has the same signature recently, skip writes.
        try:
            CommandLog = apps.get_model('agent', 'CommandLog')
            last_ok = (
                CommandLog.objects.filter(device_id=int(session.device_id), status='OK')
                .filter(Q(command__startswith='SYNC_ALL') | Q(command__startswith='SYNC_PERSONNEL') | Q(command__startswith='SYNC_ACCESS_LEVELS'))
                .exclude(executed_at__isnull=True)
                .order_by('-executed_at')
                .first()
            )
            if last_ok and sig and (sig in (getattr(last_ok, 'result', '') or '')):
                try:
                    ago = timezone.now() - last_ok.executed_at
                    if ago.total_seconds() < float(reassert_s):
                        has_users = _device_has_users()
                        # Safety guard: never short-circuit when panel appears empty.
                        # This avoids stale/noop hashes masking failed or wiped user tables.
                        if has_users is False:
                            pass
                        else:
                            return (True, f"noop hash={sig}")
                except Exception:
                    has_users = _device_has_users()
                    if has_users is False:
                        pass
                    else:
                        return (True, f"noop hash={sig}")
        except Exception:
            pass

        def _send_batched(table: str, lines: list[str]) -> tuple[bool, str]:
            if not lines:
                return (True, 'empty')
            for i in range(0, len(lines), batch_size):
                chunk = lines[i:i + batch_size]
                payload = "\r\n".join(chunk)
                resp = session.driver.update_data(table, payload, '')
                # NOTE: SDK returns 0 for success; do NOT treat it as falsy.
                try:
                    result = int(resp.get('result', -1))
                except Exception:
                    result = -1
                if result < 0:
                    return (False, f"{table}_update_failed:{resp.get('error') or resp}")

                # Read-back verification (critical): some devices/ports return success but ignore writes.
                # Verify at least one record from this batch appears in the device table.
                if table.strip().lower() == 'user':
                    try:
                        pin_probe: int | None = None
                        card_probe: str | None = None
                        first = chunk[0] if chunk else ''
                        for part in str(first or '').split('\t'):
                            if part.startswith('Pin='):
                                try:
                                    pin_probe = int(part.split('=', 1)[1])
                                except Exception:
                                    pin_probe = None
                            elif part.startswith('CardNo='):
                                card_probe = (part.split('=', 1)[1] or '').strip() or None

                        if pin_probe is not None:
                            try:
                                time.sleep(0.08)
                            except Exception:
                                pass
                            def _query_user(flt: str):
                                q0 = session.driver.query_data('user', fields='Pin,CardNo', filter=str(flt or ''), option='')
                                try:
                                    qres0 = int(q0.get('result', -1))
                                except Exception:
                                    qres0 = -1
                                qdata0 = str(q0.get('data') or '').replace('\x00', '')
                                rows0 = [ln for ln in qdata0.split('\r\n') if ln]
                                return qres0, rows0, q0

                            rows = []
                            last_q = None
                            qres = -1
                            tried = [f"Pin={pin_probe}", f"Pin='{pin_probe}'"]
                            if card_probe and str(card_probe).strip().isdigit():
                                tried.extend([f"CardNo={str(card_probe).strip()}", f"CardNo='{str(card_probe).strip()}'"])

                            for flt in tried:
                                qres, rows, last_q = _query_user(flt)
                                if qres < 0:
                                    continue
                                if len(rows) > 1:
                                    break

                            if qres < 0:
                                return (False, f"user_verify_failed:pin={pin_probe} err={(last_q or {}).get('error') or (last_q or {})}")
                            if len(rows) <= 1:
                                verify_warnings.append(f"user_verify_inconclusive:pin={pin_probe}")
                                rows = []

                            if not rows:
                                # If verification is inconclusive (no data), do not fail the entire sync.
                                # Some panels/drivers filter `query_data` results even though writes apply.
                                continue

                            # Some drivers ignore `fields=` and return a full header.
                            header = rows[0].split(',') if rows else []
                            idx_pin = None
                            idx_card = None
                            try:
                                for ii, col in enumerate(header):
                                    c = (col or '').strip().lower()
                                    if c == 'pin':
                                        idx_pin = ii
                                    elif c == 'cardno':
                                        idx_card = ii
                            except Exception:
                                idx_pin = None
                                idx_card = None

                            matched_row = None
                            try:
                                for rr in rows[1:]:
                                    vals = rr.split(',')
                                    if idx_pin is not None and idx_pin < len(vals):
                                        if str(vals[idx_pin] or '').strip() == str(pin_probe):
                                            matched_row = vals
                                            break
                            except Exception:
                                matched_row = None

                            if card_probe is not None and matched_row is not None:
                                try:
                                    if idx_card is not None and idx_card < len(matched_row):
                                        got_card = str(matched_row[idx_card] or '').strip()
                                        if got_card and got_card != card_probe:
                                            return (False, f"user_verify_mismatch:pin={pin_probe} card={got_card} expected={card_probe}")
                                except Exception:
                                    pass
                    except Exception:
                        # Verification should not prevent applying a sync if writes succeeded.
                        verify_warnings.append('user_verify_exception')

                if inter_sleep:
                    try:
                        time.sleep(inter_sleep)
                    except Exception:
                        pass
            return (True, 'ok')

        try:
            if tz_lines:
                ok_tz, info_tz = _send_batched('timezone', tz_lines)
                if not ok_tz:
                    return (False, info_tz)

            ok_u, info_u = _send_batched('user', user_lines)
            if not ok_u:
                return (False, info_u)

            if ua_lines:
                ok_ua, info_ua = _send_batched('userauthorize', ua_lines)
                if not ok_ua:
                    return (False, info_ua)

            # Hard guard against silent no-op writes (observed on some ports/proxies):
            # if we attempted to sync users but controller still appears empty, report error.
            try:
                has_users_after = _device_has_users()
            except Exception:
                has_users_after = None
            if has_users_after is False:
                return (False, 'sync_no_effect:user_table_empty_after_write')

            # Audit
            try:
                AuditLog = apps.get_model('agent', 'AuditLog')
                AuditLog.objects.create(
                    module='device',
                    action='sync_personnel',
                    entity_id=int(session.device_id),
                    entity_name=getattr(session, 'name', '') or getattr(session, 'sn', ''),
                    details=f"employees={employees.count()} doors={len(door_numbers)} tz={len(tz_ids)}",
                )
            except Exception:
                pass

            warn_txt = ''
            try:
                if verify_warnings:
                    warn_txt = ' warn=' + str(len(verify_warnings))
            except Exception:
                warn_txt = ''
            return (True, f"synced employees={employees.count()} tz={len(tz_ids)} hash={sig}{warn_txt}")
        except Exception as e:
            return (False, f"sync_failed:{e}")

    def _process_one_command(self) -> None:
        item = self.cmd_queue.pop()
        cmdlog_id_from_db: Optional[int] = None
        if not item:
            popped = self._pop_pending_command_from_db()
            if not popped:
                return
            cmdlog_id_from_db, device_id, cmd = popped
        else:
            device_id, cmd = item
        session = self.sessions.get(device_id)
        if not session or not session.connected:
            try:
                if session and not session.connected:
                    session.connect()
            except Exception:
                pass
            # Never drop commands when device is temporarily disconnected.
            # In-memory items are requeued; DB-picked rows are returned to PENDING.
            if item is not None:
                try:
                    self.enqueue_command(int(device_id), str(cmd or ''))
                except Exception:
                    pass
            elif cmdlog_id_from_db is not None:
                try:
                    CommandLog = apps.get_model('agent', 'CommandLog')
                    CommandLog.objects.filter(id=int(cmdlog_id_from_db), status='RUNNING', executed_at__isnull=True).update(
                        status='PENDING',
                        result='queued:not-connected',
                    )
                except Exception:
                    pass
            return
        # Very small parser replicating legacy prefixes
        try:
            cmdlog_id: Optional[int] = cmdlog_id_from_db
            if cmd.startswith('LOGID:'):
                try:
                    head, rest = cmd.split(' ', 1)
                    cmdlog_id = int(head.split(':', 1)[1])
                    cmd = rest.strip()
                except Exception:
                    cmdlog_id = None

            if cmd.startswith("CONNECT"):
                session.connect()
            elif cmd.startswith("DISCONNECT"):
                session.disconnect()
            elif cmd.startswith("REAL_LOG"):
                session.poll_rtlog()
            elif cmd.startswith("DOWN_NEWLOG"):
                session.down_new_logs()
            elif cmd.startswith("SYNC_TIME"):
                # Best-effort: encode time as "SYNC_TIME:YYYY-mm-dd HH:MM:SS".
                # Real drivers can implement a dedicated set-time operation later.
                ts = cmd.split(':', 1)[1].strip() if ':' in cmd else ''
                try:
                    if ts:
                        session.driver.set_options(f"time={ts}")
                    else:
                        session.driver.set_options("time=now")
                except Exception:
                    pass
            elif cmd.startswith(('SYNC_ALL', 'SYNC_PERSONNEL', 'SYNC_ACCESS_LEVELS')):
                # Enforce global rate limit for manual/in-memory commands too.
                if not self._sync_personnel_rate_peek_ok():
                    try:
                        # Requeue and yield a bit to avoid busy looping.
                        self.enqueue_command(int(device_id), cmd)
                        time.sleep(min(0.5, float(self.poll_interval or 0.5)))
                    except Exception:
                        pass
                    return
                self._sync_personnel_rate_record()
                ok, info = self._sync_personnel_to_device(session)
                if cmdlog_id is not None:
                    self._mark_command_log(cmdlog_id, status='OK' if ok else 'ERR', result=info)
            elif cmd.startswith('CLEAR_DEVICE_DATA'):
                # Clear non-event data from controller.
                # This can take a long time on some panels (notably C3-Pro), so it
                # MUST run in CommCenter, not in the web request.
                ok = True
                info_parts: list[str] = []
                try:
                    def _safe_count(table_name: str) -> int | None:
                        try:
                            cc = session.driver.Get_Data_Count(str(table_name))
                            rv = int((cc or {}).get('result', -1))
                            return rv if rv >= 0 else None
                        except Exception:
                            return None

                    # Match legacy high-level semantics (see debug_pyc/model_device.py):
                    # templatev10 (optional) -> user (required) -> usertype (optional) -> userauthorize (required)
                    required_tables = ('user', 'userauthorize')
                    optional_tables = ('templatev10', 'usertype')

                    before_counts: dict[str, int | None] = {t: _safe_count(t) for t in (*optional_tables, *required_tables)}

                    for t in optional_tables:
                        try:
                            r = session.driver.delete_data(t, '')
                            if r.get('result', -1) >= 0:
                                info_parts.append(f"{t}:ok")
                            else:
                                info_parts.append(f"{t}:skip")
                        except Exception:
                            info_parts.append(f"{t}:skip")

                    for t in required_tables:
                        r = session.driver.delete_data(t, '')
                        if r.get('result', -1) < 0:
                            ok = False
                            info_parts.append(f"{t}:err")
                            break
                        info_parts.append(f"{t}:ok")

                    # No-op guard: if table had rows before and still has >= same rows after,
                    # report explicit no-effect instead of false OK.
                    if ok:
                        for t in required_tables:
                            b = before_counts.get(t)
                            a = _safe_count(t)
                            if b is not None and a is not None and b > 0 and a >= b:
                                ok = False
                                info_parts.append(f"{t}:noeffect")
                                break
                except Exception as e:
                    ok = False
                    info_parts.append(f"err:{e}")

                if cmdlog_id is not None:
                    self._mark_command_log(
                        cmdlog_id,
                        status='OK' if ok else 'ERR',
                        result=(';'.join([p for p in info_parts if p]) or ('ok' if ok else 'err'))[:120],
                    )
            # Extend with more mappings as needed.
            elif cmd.startswith("DOOR_OPEN"):
                door = cmd.split(":", 1)[1] if ":" in cmd else "0"
                def _ok(ret: Any) -> bool:
                    try:
                        if isinstance(ret, dict):
                            r = int(ret.get('result', -1) or -1)
                            return r >= 0
                    except Exception:
                        pass
                    return bool(ret)

                acted = False
                last_err = None
                try:
                    rr = session.driver.controldevice(int(door), 1, 1)
                    acted = _ok(rr)
                except Exception as e:
                    last_err = e
                if not acted:
                    try:
                        rr2 = session.driver.control_normal_open(int(door), 1)
                        acted = _ok(rr2)
                    except Exception as e:
                        last_err = e
                if not acted:
                    raise RuntimeError(f"door_open_no_effect:{last_err}")
                self._publish_event({
                    "type": "door.open",
                    "device_id": device_id,
                    "door": door,
                    "event_description": describe_door_event_type("door.open"),
                })
                if cmdlog_id is not None:
                    self._mark_command_log(cmdlog_id, status='OK', result='done')
            elif cmd.startswith("DOOR_CLOSE"):
                door = cmd.split(":", 1)[1] if ":" in cmd else "0"
                def _ok(ret: Any) -> bool:
                    try:
                        if isinstance(ret, dict):
                            r = int(ret.get('result', -1) or -1)
                            return r >= 0
                    except Exception:
                        pass
                    return bool(ret)

                acted = False
                last_err = None
                try:
                    rr = session.driver.controldevice(int(door), 1, 0)
                    acted = _ok(rr)
                except Exception as e:
                    last_err = e
                if not acted:
                    try:
                        rr2 = session.driver.control_normal_open(int(door), 0)
                        acted = _ok(rr2)
                    except Exception as e:
                        last_err = e
                if not acted:
                    raise RuntimeError(f"door_close_no_effect:{last_err}")
                self._publish_event({
                    "type": "door.close",
                    "device_id": device_id,
                    "door": door,
                    "event_description": describe_door_event_type("door.close"),
                })
                if cmdlog_id is not None:
                    self._mark_command_log(cmdlog_id, status='OK', result='done')
            elif cmd.startswith("DOOR_NORMAL_OPEN"):
                door = cmd.split(":", 1)[1] if ":" in cmd else "0"
                def _ok(ret: Any) -> bool:
                    try:
                        if isinstance(ret, dict):
                            r = int(ret.get('result', -1) or -1)
                            return r >= 0
                    except Exception:
                        pass
                    return bool(ret)

                acted = False
                last_err = None
                try:
                    rr = session.driver.control_normal_open(int(door), 1)
                    acted = _ok(rr)
                except Exception as e:
                    last_err = e
                if not acted:
                    try:
                        rr2 = session.driver.controldevice(int(door), 1, 1)
                        acted = _ok(rr2)
                    except Exception as e:
                        last_err = e
                if not acted:
                    raise RuntimeError(f"door_normal_open_no_effect:{last_err}")
                self._publish_event({
                    "type": "door.normal_open",
                    "device_id": device_id,
                    "door": door,
                    "event_description": describe_door_event_type("door.normal_open"),
                })
                if cmdlog_id is not None:
                    self._mark_command_log(cmdlog_id, status='OK', result='done')
            elif cmd.startswith("DOOR_NORMAL_CLOSE"):
                door = cmd.split(":", 1)[1] if ":" in cmd else "0"
                def _ok(ret: Any) -> bool:
                    try:
                        if isinstance(ret, dict):
                            r = int(ret.get('result', -1) or -1)
                            return r >= 0
                    except Exception:
                        pass
                    return bool(ret)

                acted = False
                last_err = None
                try:
                    rr = session.driver.control_normal_open(int(door), 0)
                    acted = _ok(rr)
                except Exception as e:
                    last_err = e
                if not acted:
                    try:
                        rr2 = session.driver.controldevice(int(door), 1, 0)
                        acted = _ok(rr2)
                    except Exception as e:
                        last_err = e
                if not acted:
                    raise RuntimeError(f"door_normal_close_no_effect:{last_err}")
                self._publish_event({
                    "type": "door.normal_close",
                    "device_id": device_id,
                    "door": door,
                    "event_description": describe_door_event_type("door.normal_close"),
                })
                if cmdlog_id is not None:
                    self._mark_command_log(cmdlog_id, status='OK', result='done')
            elif cmd.startswith("DOOR_CANCEL_ALARM"):
                door = cmd.split(":", 1)[1] if ":" in cmd else "0"
                session.driver.cancel_alarm(door)
                self._publish_event({
                    "type": "door.cancel_alarm",
                    "device_id": device_id,
                    "door": door,
                    "event_description": describe_door_event_type("door.cancel_alarm"),
                })
                if cmdlog_id is not None:
                    self._mark_command_log(cmdlog_id, status='OK', result='done')
            elif cmd.startswith("SET_OPTION:"):
                # Set device parameters via the driver (e.g. ADMS ServerAddr/ServerPort).
                # Uses the already-open driver connection, so no bridge subprocess conflict.
                items = cmd[len("SET_OPTION:"):]
                ret = session.driver.set_options(items)
                if isinstance(ret, dict):
                    try:
                        ok = int(ret.get('result', -1)) >= 0
                    except Exception:
                        ok = bool(ret.get('result'))
                else:
                    ok = bool(ret)
                result_str = (str(ret.get('result', '')) if isinstance(ret, dict) else str(ret or ''))[:120]
                if cmdlog_id is not None:
                    self._mark_command_log(cmdlog_id, status='OK' if ok else 'ERR', result=result_str)
            elif cmd.startswith("REBOOT"):
                # Reboot device via ControlDevice(op=3). Many controllers require a reboot
                # for some communication parameters (e.g., ADMS) to take effect.
                ret = session.driver.controldevice(0, 3, 0)
                ok = False
                if isinstance(ret, dict):
                    try:
                        ok = int(ret.get('result', -1)) >= 0
                    except Exception:
                        ok = bool(ret.get('result'))
                else:
                    ok = bool(ret)

                try:
                    AuditLog = apps.get_model('agent', 'AuditLog')
                    AuditLog.objects.create(
                        module='device',
                        action='reboot',
                        entity_id=int(session.device_id),
                        entity_name=str(session.sn or session.name or ''),
                        details=str(ret)[:4000],
                    )
                except Exception:
                    pass

                if cmdlog_id is not None:
                    self._mark_command_log(cmdlog_id, status='OK' if ok else 'ERR', result='reboot')
            elif cmd.startswith("GET_OPTION:"):
                # Read device parameters via the driver using the open connection.
                # Useful for debugging ADMS config while CommCenter holds the device.
                items = cmd[len("GET_OPTION:"):].strip()
                ret = session.driver.get_options(items)
                ok = False
                data_txt = ''
                if isinstance(ret, dict):
                    try:
                        ok = int(ret.get('result', -1)) >= 0
                    except Exception:
                        ok = bool(ret.get('result'))
                    try:
                        data_txt = str(ret.get('data') or '')
                    except Exception:
                        data_txt = ''
                else:
                    ok = bool(ret)
                    data_txt = str(ret or '')

                # Durable audit of the values (truncate to keep DB sane).
                try:
                    AuditLog = apps.get_model('agent', 'AuditLog')
                    details = (data_txt or '').replace('\r\n', '\n').replace('\r', '\n')
                    if len(details) > 4000:
                        details = details[:4000] + '…'
                    AuditLog.objects.create(
                        module='device',
                        action='get_options',
                        entity_id=int(session.device_id),
                        entity_name=str(session.sn or session.name or ''),
                        details=f"items={items}\n{details}",
                    )
                except Exception:
                    pass

                if cmdlog_id is not None:
                    self._mark_command_log(cmdlog_id, status='OK' if ok else 'ERR', result='audited')
            else:
                # If a DB-originated command was allow-listed but not implemented,
                # mark it explicitly to avoid leaving it stuck in RUNNING.
                if cmdlog_id is not None:
                    self._mark_command_log(cmdlog_id, status='ERR', result='unsupported')
        except Exception as e:  # pragma: no cover
            LOG.error("Command '%s' failed for device %s: %s", cmd, device_id, e)
            try:
                if cmdlog_id_from_db is not None:
                    self._mark_command_log(int(cmdlog_id_from_db), status='ERR', result=str(e)[:120])
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Monitoring & polling
    # ------------------------------------------------------------------
    def _should_download(self) -> bool:
        # Always enforce a cooldown so we don't download on every poll.
        now_ts = time.time()
        if (now_ts - self._last_download_ts) < self.download_cooldown_s:
            return False
        current_hour = timezone.now().hour
        # If hours are not configured, enable downloads all day (but throttled above).
        if not self.download_hours:
            return True
        return current_hour in self.download_hours

    def _poll_cycle(self) -> None:
        # Commands first: keep remote open responsive even when some devices are
        # currently offline or in reconnect backoff.
        self._process_one_command()
        self.connect_all()
        # Try once more after (re)connect to avoid waiting an extra cycle.
        self._process_one_command()
        # Rtlog for each session
        for s in self.sessions.values():
            if s.connected:
                was_connected = True
                rt_lines = s.poll_rtlog()

                # If poll_rtlog() failed repeatedly it will disconnect the session.
                # Persist/broadcast the offline transition once so it is visible
                # in DB (AuditLog) and in the UI.
                if was_connected and (not s.connected):
                    ua_broadcast = None
                    try:
                        DeviceStatus = apps.get_model('agent', 'DeviceStatus')
                        obj = DeviceStatus.objects.filter(device_id=s.device_id).first()
                        if obj and bool(getattr(obj, 'online', True)):
                            obj.online = False
                            try:
                                obj.door_state = ''
                            except Exception:
                                pass
                            obj.save(update_fields=['online', 'door_state', 'updated_at'])
                            try:
                                ua = getattr(obj, 'updated_at', None)
                                if ua is not None:
                                    ua_broadcast = ua.isoformat() if hasattr(ua, 'isoformat') else str(ua)
                            except Exception:
                                ua_broadcast = None
                    except Exception:
                        ua_broadcast = None

                    if self.state_store:
                        try:
                            self.state_store.update_device(s.device_id, online=False)
                        except Exception:
                            pass
                    try:
                        from agent.ws import broadcast_device_status
                        broadcast_device_status(s.device_id, False, serial=s.sn, updated_at=ua_broadcast)
                    except Exception:
                        pass
                    continue

                # Treat successful communication (even empty rtlog) as a heartbeat.
                # poll_rtlog() sets s.fails=0 on success; it increments on failure.
                if getattr(s, 'connected', False) and int(getattr(s, 'fails', 0) or 0) == 0:
                    self._touch_last_contact(s.device_id)
                if rt_lines:
                    filtered = self._persist_rtlog(s, rt_lines)
                    self.total_rtlog_lines += len(filtered or [])
                    if self.state_store:
                        self.state_store.update_device(s.device_id, online=True)
                    if filtered:
                        self._publish_event({"type": "rtlog.batch", "device_id": s.device_id, "lines": filtered})
                # Poll incremental transaction logs frequently for low-latency UI updates.
                # Some panels produce card reads only via get_transaction(newlog=True).
                now_ts = time.time()
                last_tx = float(getattr(s, 'last_tx_poll_ts', 0.0) or 0.0)
                if (now_ts - last_tx) >= 0.5:
                    s.last_tx_poll_ts = now_ts
                    new_logs = s.down_new_logs()
                    if new_logs:
                        # Persist transaction NewRecord logs into the same realtime stream
                        # used by the Live Monitor polling endpoint. This avoids the situation
                        # where the UI receives only a subset of scans when WebSockets are
                        # connected but cross-process delivery is unavailable.
                        try:
                            filtered_tx = self._persist_rtlog(s, new_logs)
                            self.total_rtlog_lines += len(filtered_tx or [])
                        except Exception:
                            filtered_tx = None

                        codes = []
                        descs = []
                        verify_modes = []
                        card_nos = []
                        door_numbers = []
                        timestamp_strs = []
                        for raw in new_logs:
                            raw = (raw or '').strip()
                            if not raw:
                                continue
                            low = raw.lower().replace(' ', '')
                            # Some firmwares include a header line in the batch.
                            if low.startswith('pin,verified,doorid'):
                                continue

                            normalized = raw
                            if "\t" in normalized and "," not in normalized:
                                normalized = normalized.replace("\t", ",")
                            if ";" in normalized and "," not in normalized and normalized.count(';') >= 2:
                                normalized = normalized.replace(";", ",")
                            parts = [p.strip() for p in normalized.split(',')]
                            pin_for_lookup = ''

                            # Format A (standard): ts,pin,card,door,code,verify,...
                            looks_like_ts = bool(parts and (len(parts[0]) >= 10) and ('-' in parts[0]) and (parts[0][:4].isdigit()))
                            if looks_like_ts:
                                timestamp = parts[0] if parts else ''
                                pin_for_lookup = parts[1] if len(parts) > 1 else ''
                                card = parts[2] if len(parts) > 2 else ''
                                door = parts[3] if len(parts) > 3 else ''
                                code = parts[4] if len(parts) > 4 else ''
                                verify = parts[5] if len(parts) > 5 else ''
                            elif len(parts) == 7:
                                # SDK transaction format (7-field, Cardno-first):
                                # Cardno,Pin,Verified,DoorID,EventType,InOutState,Time_second
                                card = parts[0] if parts else ''
                                pin_for_lookup = parts[1] if len(parts) > 1 else ''
                                verify = parts[2] if len(parts) > 2 else ''
                                door = parts[3] if len(parts) > 3 else ''
                                code = parts[4] if len(parts) > 4 else ''
                                timestamp = parts[6] if len(parts) > 6 else ''
                            else:
                                # Format B GetRTLog (9-field, Pin-first) or 8-field variant:
                                # Pin,Verified,DoorID,EventType,InOutState,Time_second,Index,Cardno,Sitecode
                                pin_for_lookup = str(parts[0]).strip() if parts else ''
                                timestamp = parts[5] if len(parts) > 5 else ''
                                door = parts[2] if len(parts) > 2 else ''
                                code = parts[3] if len(parts) > 3 else ''
                                verify = parts[1] if len(parts) > 1 else ''
                                card = parts[7] if len(parts) > 7 else (parts[6] if len(parts) > 6 else '')
                                # Only consider the 7th field as a CardNo candidate in the
                                # 8-field variant (no Index). In the 9-field variant, parts[6]
                                # is the Index and must not be treated as a CardNo.
                                if (not str(card or '').strip()) and len(parts) > 6 and len(parts) < 9:
                                    cand = str(parts[6] or '').strip()
                                    if cand:
                                        is_numeric = cand.isdigit()
                                        if (not is_numeric) or (is_numeric and len(cand) >= 7):
                                            card = cand

                            card = re.sub(r'[^0-9A-Za-z]+', '', str(card or '')).upper()
                            if (not card) and pin_for_lookup:
                                looked_up = self._lookup_card_for_pin(s, pin_for_lookup)
                                looked_up = re.sub(r'[^0-9A-Za-z]+', '', str(looked_up or '')).upper()
                                if looked_up and looked_up not in {'0', '000000', '0000000', '00000000'}:
                                    card = looked_up

                            codes.append(code)
                            descs.append(describe_event_code(code))
                            verify_modes.append(describe_verify_mode(verify))
                            card_nos.append(card)
                            door_numbers.append(door)
                            timestamp_strs.append(timestamp)
                        self._persist_event_logs(s, new_logs)
                        self.total_event_logs += len(new_logs)
                        self._publish_event({
                            "type": "event.batch",
                            "device_id": s.device_id,
                            "count": len(codes),
                            "codes": codes,
                            "descriptions": descs,
                            "verify_modes": verify_modes,
                            "card_nos": card_nos,
                            "door_numbers": door_numbers,
                            "timestamps": timestamp_strs,
                        })
        self.heartbeat_backend.set("last_cycle", time.time())
        self.cycles += 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run_forever(self) -> None:
        LOG.info("ModernCommCenter starting with %d devices", len(self.sessions))
        while not self._stop.is_set():
            self._poll_cycle()
            time.sleep(self.poll_interval)
        LOG.info("ModernCommCenter stopped")

    def stop(self) -> None:
        self._stop.set()
        for s in self.sessions.values():
            if s.connected:
                s.disconnect()

    def run_once(self) -> None:
        """Execute a single poll cycle (useful for testing)."""
        self._poll_cycle()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _normalize_rtlog_line(self, raw: str) -> str:
        raw = (raw or '').strip()
        if not raw:
            return ''
        # Many devices return tab-separated fields; the monitor expects comma-separated.
        if "\t" in raw and "," not in raw:
            raw = raw.replace("\t", ",")
        # Some firmware variants use ';' as separator.
        if ";" in raw and "," not in raw and raw.count(';') >= 2:
            raw = raw.replace(";", ",")
        return raw.strip()

    def _refresh_panel_card_cache(self, session: 'DeviceSession') -> None:
        """Download user\u2192card mapping from panel and store in per-device cache."""
        import time as _time
        dev_id = session.device_id
        now = _time.monotonic()
        last = self._panel_card_cache_ts.get(dev_id, 0.0)
        if now - last < self.panel_card_cache_ttl and dev_id in self._panel_card_cache:
            return  # still fresh
        try:
            mapping = session.driver.get_panel_user_card_map()
            if mapping:
                self._panel_card_cache[dev_id] = mapping
                self._panel_card_cache_ts[dev_id] = now
                LOG.info('panel_card_cache refreshed device=%s entries=%d', session.sn, len(mapping))
            else:
                LOG.debug('panel_card_cache empty device=%s', session.sn)
        except Exception as exc:
            LOG.debug('panel_card_cache refresh failed device=%s: %s', session.sn, exc)

    def _lookup_card_for_pin(self, session: 'DeviceSession', pin: str) -> str:
        pin = str(pin or '').strip()
        if not pin or pin in ('0',):
            return ''
        dev_id = int(getattr(session, 'device_id', 0) or 0)
        try:
            # Ensure panel cache is reasonably fresh.
            import time as _time
            last = float(self._panel_card_cache_ts.get(dev_id, 0.0) or 0.0)
            if (_time.monotonic() - last) > float(self.panel_card_cache_ttl or 0.0):
                self._refresh_panel_card_cache(session)
        except Exception:
            pass

        try:
            panel_map = self._panel_card_cache.get(dev_id) or {}
            card = str(panel_map.get(pin, '') or '').strip()
            if card and card not in ('0', '00000000'):
                return card
        except Exception:
            pass
        # Hard requirement: never use the Django DB as a source of CardNo.
        # If the controller didn't provide CardNo (rtlog/transaction/user table), return empty.
        return ''

    def _persist_rtlog(self, session: DeviceSession, lines: List[str]) -> List[str]:
        try:
            import time as _time
            from django.core.cache import cache
            import re

            # ------------------------------------------------------------------
            # PIN\u2192card enrichment: controller only
            # 1. Panel user table cache (actual Wiegand card numbers enrolled on panel)
            # Refresh panel cache if stale (TTL check via _refresh_panel_card_cache).
            # ------------------------------------------------------------------
            import time as _time2
            _panel_map = self._panel_card_cache.get(session.device_id)
            _last_refresh = self._panel_card_cache_ts.get(session.device_id, 0.0)
            if _panel_map is None or (_time2.monotonic() - _last_refresh) > self.panel_card_cache_ttl:
                self._refresh_panel_card_cache(session)
                _panel_map = self._panel_card_cache.get(session.device_id, {})
            else:
                _panel_map = _panel_map or {}

            def _lookup_card_for_pin(pin: str) -> str:
                """Return card number for PIN, from the controller only.

                Hard requirement for live monitor: CardNo must be sourced from
                the controller (including denied/unregistered cards) rather than
                the Django DB.
                """
                card = _panel_map.get(pin, '')
                if card and card not in ('0', '00000000'):
                    return card
                return ''

            # Filter duplicates and obvious heartbeat/noise lines.
            # Uses a rolling hash set per device to catch ring-buffer re-reads after reconnect.
            dev_id_rtlog = session.device_id
            seen_set = self._rtlog_seen.get(dev_id_rtlog)
            seen_order = self._rtlog_seen_order.get(dev_id_rtlog)
            if seen_set is None:
                seen_set = set()
                self._rtlog_seen[dev_id_rtlog] = seen_set
            if seen_order is None:
                seen_order = deque(maxlen=self.rtlog_dedupe_window)
                self._rtlog_seen_order[dev_id_rtlog] = seen_order

            filtered: List[str] = []
            last = self._rtlog_last_line.get(session.device_id)
            for raw in lines:
                raw = self._normalize_rtlog_line(str(raw or ''))
                if not raw:
                    continue
                low = raw.lower().replace(' ', '')
                # Header/noise line from some firmwares.
                if low.startswith('pin,verified,doorid'):
                    continue
                parts = [p.strip() for p in raw.split(',')]
                # Detect Format A (starts with timestamp) vs Format B (pin,verified,...).
                _looks_ts = bool(
                    parts and len(parts[0]) >= 10 and '-' in parts[0] and parts[0][:4].isdigit()
                )
                if _looks_ts:
                    # Format A: ts,pin,card,door,code,verify,...
                    card = parts[2] if len(parts) > 2 else ''
                    door = parts[3] if len(parts) > 3 else ''
                    code = parts[4] if len(parts) > 4 else ''
                    # Drop noisy repeats that look like a keepalive (no card, no door).
                    if code == '200' and (card in ('', '0', '000000', '00000000')) and (door in ('', '0')):
                        last = raw
                        continue
                    # Deduplicate Format A by a fingerprint that includes CardNo.
                    # Important: some firmwares only provide second-resolution timestamps,
                    # and for denied/unregistered cards PIN may be 0/empty.
                    pin_a = parts[1] if len(parts) > 1 else ''
                    fp_a = f"{parts[0]}|{pin_a}|{card}|{door}|{code}"
                    if fp_a in seen_set:
                        last = raw
                        continue
                    while len(seen_order) >= self.rtlog_dedupe_window:
                        try: seen_set.discard(seen_order.popleft())
                        except Exception: pass
                    seen_set.add(fp_a)
                    seen_order.append(fp_a)
                else:
                    # Format B: pin,verified,door,eventType,inOut,time_second[,index][,cardno,sitecode]
                    pin_b = str(parts[0]).strip() if parts else ''
                    # Cardno is at index 7 when 9+ parts (with index field) or index 6 for 8 parts.
                    card_idx = 7 if len(parts) >= 9 else 6
                    card_b = str(parts[card_idx]).strip() if len(parts) > card_idx else ''
                    # Deduplicate Format B by a stable per-event fingerprint.
                    # IMPORTANT: many firmwares only provide second-resolution time;
                    # repeated scans within the same second may still be unique via the 'Index' field.
                    ts_b = str(parts[5]).strip() if len(parts) > 5 else ''
                    door_b = str(parts[2]).strip() if len(parts) > 2 else ''
                    etype_b = str(parts[3]).strip() if len(parts) > 3 else ''
                    idx_b = str(parts[6]).strip() if len(parts) >= 9 and len(parts) > 6 else ''
                    fp_b = f"{ts_b}|{pin_b}|{door_b}|{etype_b}|{idx_b}|{card_b}"
                    if fp_b in seen_set:
                        last = raw
                        continue
                    while len(seen_order) >= self.rtlog_dedupe_window:
                        try: seen_set.discard(seen_order.popleft())
                        except Exception: pass
                    seen_set.add(fp_b)
                    seen_order.append(fp_b)
                    # Enrich: if cardno is missing, look it up (panel user table → Django DB).
                    if (not card_b or card_b in ('0',)) and pin_b and pin_b not in ('0', ''):
                        looked_up = _lookup_card_for_pin(pin_b)
                        if looked_up:
                            parts_mut = list(parts)
                            while len(parts_mut) <= card_idx:
                                parts_mut.append('')
                            parts_mut[card_idx] = looked_up
                            raw = ','.join(parts_mut)
                            LOG.debug(
                                "rtlog enrich pin=%s card=%s device=%s",
                                pin_b, looked_up, session.sn,
                            )
                filtered.append(raw)
                last = raw

                # Fast-path cache for card enrollment UI (controller readers only):
                # store most recent non-empty card number so /api/cards/read/wait/
                # can return it instantly without DB scans or 1s sleeps.
                try:
                    parts_cache = [p.strip() for p in str(raw or '').split(',')]
                    looks_ts_cache = bool(
                        parts_cache
                        and len(parts_cache[0]) >= 10
                        and '-' in parts_cache[0]
                        and parts_cache[0][:4].isdigit()
                    )
                    if looks_ts_cache:
                        card_cache = parts_cache[2] if len(parts_cache) > 2 else ''
                        door_cache = parts_cache[3] if len(parts_cache) > 3 else ''
                    else:
                        door_cache = parts_cache[2] if len(parts_cache) > 2 else ''
                        # Format B: pin,verified,door,eventType,inOut,time_second[,index],cardno,sitecode
                        if len(parts_cache) >= 9:
                            card_cache = parts_cache[7] if len(parts_cache) > 7 else ''
                        else:
                            card_cache = parts_cache[6] if len(parts_cache) > 6 else ''
                    card_cache = re.sub(r'[^0-9A-Za-z]+', '', str(card_cache or '')).upper()
                    if card_cache and card_cache not in {'0', '000000', '0000000', '00000000'}:
                        cache.set(
                            'agent:last_card_read',
                            {
                                'card_number': card_cache,
                                'card_number_raw': card_cache,
                                'source': 'controller_rtlog',
                                'device_id': int(session.device_id or 0),
                                'door_number': str(door_cache or ''),
                            },
                            timeout=30,
                        )
                except Exception:
                    pass
            self._rtlog_last_line[session.device_id] = last or self._rtlog_last_line.get(session.device_id, '')

            from agent import models  # needed for persistence only
            objs = [models.DeviceRealtimeLog(device_id=session.device_id, sn=session.sn, raw=raw) for raw in filtered]
            models.DeviceRealtimeLog.objects.bulk_create(objs, ignore_conflicts=True)
            if self.state_store:
                for raw in filtered:
                    parts = raw.split(',')
                    if len(parts) > 4:
                        # door is typically at index 3 (index 4 is event code)
                        door = parts[3]
                        self.state_store.update_door(session.device_id, door, 'activity')
            return filtered
        except Exception as e:  # pragma: no cover
            LOG.warning("Persist rtlog failed device=%s: %s", session.sn, e)
            return []

    def _persist_event_logs(self, session: DeviceSession, lines: List[str]) -> None:
        try:
            from agent import models
            # Filter duplicates for this device (both within batch and across recent batches)
            dev_id = session.device_id
            recent = self._event_recent.get(dev_id)
            order = self._event_recent_order.get(dev_id)
            if recent is None:
                recent = set()
                self._event_recent[dev_id] = recent
            if order is None:
                order = deque(maxlen=self.event_dedupe_window)
                self._event_recent_order[dev_id] = order

            filtered: List[str] = []
            for raw in lines:
                raw = (raw or '').strip()
                if not raw:
                    continue
                if raw in recent:
                    continue
                filtered.append(raw)
                recent.add(raw)
                order.append(raw)
                # deque maxlen handles trimming order; we need to trim set accordingly
                while len(order) > self.event_dedupe_window:
                    old = order.popleft()
                    try:
                        recent.discard(old)
                    except Exception:
                        pass

            objs = []
            for raw in filtered:
                raw = (raw or '').strip()
                if not raw:
                    continue
                low = raw.lower().replace(' ', '')
                if low.startswith('pin,verified,doorid'):
                    continue
                parts = [p.strip() for p in raw.split(',')]
                looks_like_ts = bool(parts and (len(parts[0]) >= 10) and ('-' in parts[0]) and (parts[0][:4].isdigit()))
                if looks_like_ts:
                    timestamp = parts[0] if parts else ''
                    code = parts[4] if len(parts) > 4 else ''
                else:
                    # Transaction format (see above): store `time_second` as timestamp_str and `eventType` as code.
                    timestamp = parts[5] if len(parts) > 5 else ''
                    code = parts[3] if len(parts) > 3 else ''
                objs.append(models.DeviceEventLog(
                    device_id=session.device_id,
                    sn=session.sn,
                    timestamp_str=timestamp,
                    code=code,
                    raw_line=raw,
                ))
            if objs:
                models.DeviceEventLog.objects.bulk_create(objs, ignore_conflicts=True)
            if self.state_store:
                for raw in filtered:
                    parts = raw.split(',')
                    # door is typically at index 3 (index 4 is event code)
                    door = parts[3] if len(parts) > 3 else '0'
                    self.state_store.update_door(session.device_id, door, 'event')
        except Exception as e:  # pragma: no cover
            LOG.warning("Persist event logs failed device=%s: %s", session.sn, e)

    def _publish_event(self, payload: Dict[str, Any]) -> None:
        if not self._channel_layer:
            return
        try:
            try:
                LOG.info('ModernCommCenter._publish_event -> monitor payload=%s', payload)
            except Exception:
                pass
            # Avoid stdout fallback; structured logging above is sufficient
            async_to_sync(self._channel_layer.group_send)(
                "monitor", {"type": "monitor_event", "payload": payload}
            )
        except Exception:  # pragma: no cover
            pass


# ----------------------------------------------------------------------
# Driver stubs (for development/testing without hardware)
# ----------------------------------------------------------------------
class StubDriver(object):
    """A stub driver simulating success responses with no real hardware."""

    def __init__(self, dev):
        self.dev = dev
        self._connected = False

    def connect(self):
        self._connected = True
        return {"result": 1, "hcommpro": 1}

    def disconnect(self):
        self._connected = False
        return {"result": 1}

    def get_transaction(self, newlog=False):
        if not self._connected:
            return {"result": -1}
        if newlog:
            return {"result": 2, "data": {1: "2025-11-20 10:00:00,1,0,0,100,0,0", 2: "2025-11-20 10:01:00,1,0,0,101,0,0"}}
        return {"result": 0, "data": {}}

    def get_rtlog(self):
        if not self._connected:
            return {"result": -1}
        return {"result": 1, "data": "2025-11-20 10:00:05,1,0,0,200,0,0\r\n"}

    # Remaining interface methods return neutral success
    def query_data(self, table, fields, flt, extra):
        return {"result": 0, "data": []}

    def update_data(self, table, data, extra):
        return {"result": 1}

    def delete_data(self, table, flt):
        return {"result": 1}

    def Get_Data_Count(self, table):
        return {"result": 0, "data": 0}

    def controldevice(self, door, index, state):
        return {"result": 1}

    def control_normal_open(self, door, state):
        return {"result": 1}

    def cancel_alarm(self, door):
        return {"result": 1}

    def get_options(self, items):
        return {"result": 1, "data": {}}

    def set_options(self, items):
        return {"result": 1}


class HeartbeatOnlyDriver(StubDriver):
    """Driver used for demo/virtual devices to keep liveness moving.

    It intentionally does NOT fabricate rtlog/event data; it only provides
    successful calls so CommCenter can update Device.last_contact.
    """

    def get_transaction(self, newlog=False):
        if not self._connected:
            return {"result": -1}
        return {"result": 0, "data": {}}

    def get_rtlog(self):
        if not self._connected:
            return {"result": -1}
        return {"result": 0, "data": ""}


class LegacyDriverAdapter(StubDriver):
    """Real driver adapter scaffold.

    Attempts socket connectivity if `com_address` and `com_port` are
    present on the device record. Falls back to stub behavior. Hook
    points (`_socket_*`) can later be replaced by SDK / DLL calls.
    """
    def __init__(self, dev):
        super().__init__(dev)
        self._sock = None
        # Support both legacy fields (com_address/com_port) and the modern Device
        # schema (ip_address/port). The tray launcher uses the modern schema.
        self._addr = getattr(dev, 'ip_address', None) or getattr(dev, 'com_address', None)
        self._port = getattr(dev, 'port', None) or getattr(dev, 'com_port', None)

    def _allow_stub_fallback(self) -> bool:
        # IMPORTANT: StubDriver generates simulated logs (Door Open/Close, RTLOG noise).
        # In real deployments we must not fabricate events when hardware is unreachable.
        return str(os.getenv('COMM_ALLOW_STUB_FALLBACK', '') or '').strip().lower() in (
            '1', 'true', 'yes', 'y', 'on'
        )

    def _socket_connect(self):  # pragma: no cover (network optional)
        if not (self._addr and self._port):
            return False
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect((self._addr, int(self._port)))
            self._sock = s
            return True
        except Exception:
            return False

    def _socket_disconnect(self):  # pragma: no cover
        try:
            if self._sock:
                self._sock.close()
        finally:
            self._sock = None

    def connect(self):
        if self._socket_connect():
            return {"result": 1, "hcommpro": 1, "transport": "socket"}
        if self._allow_stub_fallback():
            return super().connect()
        return {"result": -1, "error": "connect_failed"}

    def disconnect(self):
        if self._sock:
            self._socket_disconnect()
            return {"result": 1}
        if self._allow_stub_fallback():
            return super().disconnect()
        return {"result": 1}

    def get_transaction(self, newlog=False):
        # If we only have a raw TCP socket probe (no SDK/protocol), do not fabricate
        # logs/transactions. Return a neutral empty result so CommCenter can use this
        # as a liveness heartbeat without creating fake events.
        if self._sock is not None:
            return {"result": 0, "data": {}}
        if not self._allow_stub_fallback():
            return {"result": -1, "error": "not_connected"}
        return super().get_transaction(newlog=newlog)

    def get_rtlog(self):
        # Same logic as get_transaction: when only TCP connectivity is known, return
        # empty rtlog instead of simulated lines.
        if self._sock is not None:
            return {"result": 0, "data": ""}
        if not self._allow_stub_fallback():
            return {"result": -1, "error": "not_connected"}
        return super().get_rtlog()


def build_and_run_stub(poll_interval=1.0,
                       use_redis: bool = False,
                       redis_url: Optional[str] = None,
                       download_hours: Optional[List[int]] = None,
                       driver: str = "auto",
                       driver_factory: Optional[Callable] = None,
                       start_thread: bool = True):
    queue_backend = None
    heartbeat_backend = None
    if use_redis and redis:
        try:
            url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            client = redis.Redis.from_url(url)
            client.ping()
            queue_backend = RedisQueue(client)
            heartbeat_backend = RedisHeartbeat(client)
            LOG.info("Using Redis backends at %s", url)
        except Exception as e:  # pragma: no cover
            LOG.warning("Redis unavailable (%s); falling back to memory", e)
    center = ModernCommCenter(poll_interval=poll_interval,
                              download_hours=download_hours,
                              queue_backend=queue_backend,
                              heartbeat_backend=heartbeat_backend)

    def _is_virtual_tcp_device(dev) -> bool:
        """Treat TCP devices without an IP as virtual/test devices.

        This keeps the dashboard/DB liveness (last_contact) moving in dev/demo
        setups where a controller row exists but has no actual network target.
        """
        try:
            if not bool(getattr(dev, 'enabled', True)):
                return False
            if bool(getattr(dev, 'scanner_linked', False)):
                return False
            if str(getattr(dev, 'comm_mode', 'tcp') or 'tcp').lower() != 'tcp':
                return False
            ip = getattr(dev, 'ip_address', None) or getattr(dev, 'com_address', None)
            return not bool(ip)
        except Exception:
            return False

    def _is_demo_device(dev) -> bool:
        """Detect demo/test/virtual rows that should run in heartbeat-only mode."""
        try:
            if not bool(getattr(dev, 'enabled', True)):
                return False
            if bool(getattr(dev, 'scanner_linked', False)):
                return False
            name = str(getattr(dev, 'name', '') or '').upper()
            sn = str(getattr(dev, 'serial_number', '') or '').upper()
            for marker in ('VIRTUAL', 'DEMO', 'TEST'):
                if marker in name or marker in sn:
                    return True
            return False
        except Exception:
            return False
    # Choose driver
    if driver_factory is None:
        if driver == "stub":
            driver_factory = lambda dev: StubDriver(dev)
        elif driver == "socket":
            driver_factory = lambda dev: LegacyDriverAdapter(dev)
        elif driver == "zk":  # NEW: ZKTech native socket driver
            try:
                from .drivers.zk_socket_driver import ZKTechSocketDriver
                driver_factory = lambda dev: ZKTechSocketDriver(dev)
                LOG.info("Using ZKTech socket driver")
            except Exception as e:
                LOG.warning("ZKTech driver not available (%s); falling back to stub", e)
                driver_factory = lambda dev: StubDriver(dev)
        elif driver == "plcommpro":
            try:
                from .drivers.plcommpro_bridge_driver import PlcommproBridgeDriver
                driver_factory = lambda dev: PlcommproBridgeDriver(dev)
                LOG.info("Using plcommpro.dll bridge driver")
            except Exception as e:
                LOG.warning("plcommpro bridge driver not available (%s); falling back to stub", e)
                driver_factory = lambda dev: StubDriver(dev)
        elif driver == "sdk":
            try:
                from .driver_ctypes import get_sdk_adapter_class
                cls = get_sdk_adapter_class()
                driver_factory = (lambda dev, C=cls: C(dev)) if cls else (lambda dev: StubDriver(dev))
            except Exception:
                driver_factory = lambda dev: StubDriver(dev)
        else:  # auto
            # Prefer plcommpro bridge when available (works with 32-bit plcommpro.dll on 64-bit OS)
            try:
                from .plcommpro_bridge import bridge_available

                if bridge_available():
                    from .drivers.plcommpro_bridge_driver import PlcommproBridgeDriver

                    driver_factory = lambda dev: PlcommproBridgeDriver(dev)
                    LOG.info("Auto driver: using plcommpro bridge")
                else:
                    raise RuntimeError("plcommpro bridge unavailable")
            except Exception:
                # Prefer the pure-python ZKTech socket driver when present; it can retrieve RTLOG.
                # If unavailable, fall back to SDK (ctypes) and finally to the lightweight socket
                # probe adapter (heartbeat-only; does NOT retrieve RTLOG).
                try:
                    from .drivers.zk_socket_driver import ZKTechSocketDriver

                    driver_factory = lambda dev: ZKTechSocketDriver(dev)
                    LOG.info("Auto driver: using ZKTech socket driver")
                except Exception:
                    # Fallback to SDK (ctypes) if available, else to lightweight socket probe adapter.
                    try:
                        from .driver_ctypes import get_sdk_adapter_class

                        cls = get_sdk_adapter_class()
                        if cls:
                            driver_factory = lambda dev, C=cls: C(dev)
                            LOG.info("Auto driver: using SDK adapter")
                        else:
                            driver_factory = lambda dev: LegacyDriverAdapter(dev)
                            LOG.info("Auto driver: using legacy socket probe adapter")
                    except Exception:
                        driver_factory = lambda dev: LegacyDriverAdapter(dev)
                        LOG.info("Auto driver: using legacy socket probe adapter")

    # Per-device override: keep virtual/unconfigured TCP devices alive in dev/demo.
    # This does NOT affect real networked devices; it only applies when there's no IP.
    if driver_factory is not None:
        base_factory = driver_factory

        def driver_factory(dev):
            if _is_demo_device(dev):
                return HeartbeatOnlyDriver(dev)
            if _is_virtual_tcp_device(dev):
                return HeartbeatOnlyDriver(dev)
            return base_factory(dev)

    center.build_sessions(driver_factory)
    if start_thread:
        t = threading.Thread(target=center.run_forever, daemon=True)
        t.start()
    return center
