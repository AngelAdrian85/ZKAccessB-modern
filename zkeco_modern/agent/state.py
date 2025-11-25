"""In-memory + optional Redis-backed device/door state management."""

import time
import json
import threading
from typing import Dict, Any, Optional

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None


class DeviceStateStore(object):
    def __init__(self, redis_url: Optional[str] = None):
        self._lock = threading.Lock()
        self._data: Dict[int, Dict[str, Any]] = {}
        self.redis = None
        if redis_url and redis:
            try:
                self.redis = redis.Redis.from_url(redis_url)
                self.redis.ping()
            except Exception:
                self.redis = None

    def update_device(self, device_id: int, **fields):
        with self._lock:
            rec = self._data.setdefault(device_id, {"online": False, "last_seen": 0, "doors": {}})
            rec.update(fields)
            if "online" in fields:
                rec["last_seen"] = time.time()
        if self.redis:
            key = f"commcenter:device:{device_id}"
            doc = json.dumps(self._data[device_id])
            try:
                self.redis.set(key, doc)
            except Exception:  # pragma: no cover
                pass

    def get_snapshot(self) -> Dict[int, Dict[str, Any]]:
        with self._lock:
            return json.loads(json.dumps(self._data))  # deep copy

    def update_door(self, device_id: int, door: str, status: str):
        with self._lock:
            rec = self._data.setdefault(device_id, {"online": False, "last_seen": 0, "doors": {}})
            rec["doors"][door] = {"status": status, "ts": time.time()}
        if self.redis:
            key = f"commcenter:device:{device_id}:doors"
            try:
                self.redis.hset(key, door, status)
            except Exception:  # pragma: no cover
                pass
