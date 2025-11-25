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
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Tuple, Callable

from django.conf import settings
from django.utils import timezone
from django.db import transaction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .event_codes import describe as describe_event_code

try:  # Redis optional
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None

try:
    from legacy_models.models import Device  # fallback shim
except Exception:  # pragma: no cover
    Device = None  # type: ignore

LOG = logging.getLogger("modern_comm_center")


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
    config: Dict[str, Any] = field(default_factory=dict)

    def connect(self) -> bool:
        ret = self.driver.connect()
        ok = ret.get("result", -1) >= 0 or ret.get("hcommpro", 0) > 0
        self.connected = ok
        self.last_connect_ts = time.time()
        LOG.debug("connect device=%s result=%s", self.sn, ret)
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
                    sn=getattr(dev, "sn", ""),
                    name=getattr(dev, "device_name", ""),
                    driver=driver,
                    config={"com_address": getattr(dev, "com_address", None), "com_port": getattr(dev, "com_port", None)},
                )
                self.sessions[dev.id] = session
            except Exception as e:  # pragma: no cover
                LOG.error("Failed to init session for device %s: %s", dev.id, e)

    def connect_all(self) -> None:
        for session in self.sessions.values():
            if not session.connected:
                if session.connect():
                    if self.state_store:
                        self.state_store.update_device(session.device_id, online=True)
                    self._publish_event({"type": "device.online", "device_id": session.device_id, "sn": session.sn})

    # ------------------------------------------------------------------
    # Command handling
    # ------------------------------------------------------------------
    def enqueue_command(self, device_id: int, cmd: str) -> None:
        self.cmd_queue.push(device_id, cmd)

    def _process_one_command(self) -> None:
        item = self.cmd_queue.pop()
        if not item:
            return
        device_id, cmd = item
        session = self.sessions.get(device_id)
        if not session or not session.connected:
            return
        # Very small parser replicating legacy prefixes
        try:
            if cmd.startswith("CONNECT"):
                session.connect()
            elif cmd.startswith("DISCONNECT"):
                session.disconnect()
            elif cmd.startswith("REAL_LOG"):
                session.poll_rtlog()
            elif cmd.startswith("DOWN_NEWLOG"):
                session.down_new_logs()
            # Extend with more mappings as needed.
            elif cmd.startswith("DOOR_OPEN"):
                door = cmd.split(":", 1)[1] if ":" in cmd else "0"
                session.driver.controldevice(int(door), 1, 1)
                self._publish_event({"type": "door.open", "device_id": device_id, "door": door})
            elif cmd.startswith("DOOR_CLOSE"):
                door = cmd.split(":", 1)[1] if ":" in cmd else "0"
                session.driver.controldevice(int(door), 1, 0)
                self._publish_event({"type": "door.close", "device_id": device_id, "door": door})
            elif cmd.startswith("DOOR_NORMAL_OPEN"):
                door = cmd.split(":", 1)[1] if ":" in cmd else "0"
                session.driver.control_normal_open(int(door), 1)
                self._publish_event({"type": "door.normal_open", "device_id": device_id, "door": door})
            elif cmd.startswith("DOOR_CANCEL_ALARM"):
                door = cmd.split(":", 1)[1] if ":" in cmd else "0"
                session.driver.cancel_alarm(door)
                self._publish_event({"type": "door.cancel_alarm", "device_id": device_id, "door": door})
        except Exception as e:  # pragma: no cover
            LOG.error("Command '%s' failed for device %s: %s", cmd, device_id, e)

    # ------------------------------------------------------------------
    # Monitoring & polling
    # ------------------------------------------------------------------
    def _should_download(self) -> bool:
        if not self.download_hours:
            return False
        current_hour = timezone.now().hour
        return current_hour in self.download_hours

    def _poll_cycle(self) -> None:
        self.connect_all()
        # Commands first
        self._process_one_command()
        # Rtlog for each session
        for s in self.sessions.values():
            if s.connected:
                rt_lines = s.poll_rtlog()
                if rt_lines:
                    self._persist_rtlog(s, rt_lines)
                    self.total_rtlog_lines += len(rt_lines)
                    if self.state_store:
                        self.state_store.update_device(s.device_id, online=True)
                    self._publish_event({"type": "rtlog.batch", "device_id": s.device_id, "lines": rt_lines})
                if self._should_download():
                    new_logs = s.down_new_logs()
                    if new_logs:
                        codes = []
                        descs = []
                        for raw in new_logs:
                            parts = raw.split(',')
                            code = parts[4] if len(parts) > 4 else ''
                            codes.append(code)
                            descs.append(describe_event_code(code))
                        self._persist_event_logs(s, new_logs)
                        self.total_event_logs += len(new_logs)
                        self._publish_event({
                            "type": "event.batch",
                            "device_id": s.device_id,
                            "count": len(new_logs),
                            "codes": codes,
                            "descriptions": descs,
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
    def _persist_rtlog(self, session: DeviceSession, lines: List[str]) -> None:
        try:
            from zkeco_modern.agent import models  # fully-qualified to avoid app_label mismatch
            objs = [
                models.DeviceRealtimeLog(
                    device_id=session.device_id,
                    sn=session.sn,
                    raw=raw,
                ) for raw in lines
            ]
            models.DeviceRealtimeLog.objects.bulk_create(objs, ignore_conflicts=True)
            if self.state_store:
                for raw in lines:
                    parts = raw.split(',')
                    if len(parts) > 4:
                        door = parts[4]
                        self.state_store.update_door(session.device_id, door, 'activity')
        except Exception as e:  # pragma: no cover
            LOG.warning("Persist rtlog failed device=%s: %s", session.sn, e)

    def _persist_event_logs(self, session: DeviceSession, lines: List[str]) -> None:
        try:
            from zkeco_modern.agent import models
            objs = []
            for raw in lines:
                parts = raw.split(',')
                timestamp = parts[0] if parts else ''
                code = parts[4] if len(parts) > 4 else ''
                objs.append(models.DeviceEventLog(
                    device_id=session.device_id,
                    sn=session.sn,
                    timestamp_str=timestamp,
                    code=code,
                    raw_line=raw,
                ))
            models.DeviceEventLog.objects.bulk_create(objs, ignore_conflicts=True)
            if self.state_store:
                for raw in lines:
                    parts = raw.split(',')
                    door = parts[4] if len(parts) > 4 else '0'
                    self.state_store.update_door(session.device_id, door, 'event')
        except Exception as e:  # pragma: no cover
            LOG.warning("Persist event logs failed device=%s: %s", session.sn, e)

    def _publish_event(self, payload: Dict[str, Any]) -> None:
        if not self._channel_layer:
            return
        try:
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


class LegacyDriverAdapter(StubDriver):
    """Real driver adapter scaffold.

    Attempts socket connectivity if `com_address` and `com_port` are
    present on the device record. Falls back to stub behavior. Hook
    points (`_socket_*`) can later be replaced by SDK / DLL calls.
    """
    def __init__(self, dev):
        super().__init__(dev)
        self._sock = None
        self._addr = getattr(dev, 'com_address', None)
        self._port = getattr(dev, 'com_port', None)

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
        return super().connect()

    def disconnect(self):
        if self._sock:
            self._socket_disconnect()
            return {"result": 1}
        return super().disconnect()


def build_and_run_stub(poll_interval=1.0,
                       use_redis: bool = False,
                       redis_url: Optional[str] = None,
                       download_hours: Optional[List[int]] = None,
                       driver: str = "auto",
                       driver_factory: Optional[Callable] = None):
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
    # Choose driver
    if driver_factory is None:
        if driver == "stub":
            driver_factory = lambda dev: StubDriver(dev)
        elif driver == "socket":
            driver_factory = lambda dev: LegacyDriverAdapter(dev)
        elif driver == "sdk":
            try:
                from .driver_ctypes import get_sdk_adapter_class
                cls = get_sdk_adapter_class()
                driver_factory = (lambda dev, C=cls: C(dev)) if cls else (lambda dev: StubDriver(dev))
            except Exception:
                driver_factory = lambda dev: StubDriver(dev)
        else:  # auto
            # try sdk then socket then stub
            try:
                from .driver_ctypes import get_sdk_adapter_class
                cls = get_sdk_adapter_class()
                if cls:
                    driver_factory = lambda dev, C=cls: C(dev)
                else:
                    driver_factory = lambda dev: LegacyDriverAdapter(dev)
            except Exception:
                driver_factory = lambda dev: LegacyDriverAdapter(dev)
    center.build_sessions(driver_factory)
    t = threading.Thread(target=center.run_forever, daemon=True)
    t.start()
    return center
