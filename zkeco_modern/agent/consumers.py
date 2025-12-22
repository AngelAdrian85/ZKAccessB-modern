import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

try:  # Lazy import; if migrations not yet run we degrade gracefully
    from agent.models import Device
except Exception:  # pragma: no cover
    Device = None


class MonitorConsumer(AsyncWebsocketConsumer):
    group_name = "monitor"

    async def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close(); return
        await self.channel_layer.group_add(self.group_name, self.channel_name)  # type: ignore
        await self.accept()
        await self._send_initial_status()

    async def disconnect(self, code):  # pragma: no cover
        await self.channel_layer.group_discard(self.group_name, self.channel_name)  # type: ignore

    async def receive(self, text_data=None, bytes_data=None):  # pragma: no cover
        # Client messages ignored for now.
        pass

    async def monitor_event(self, event):
        # External broadcasts (door actions, status updates)
        payload = event.get("payload", {})
        try:
            # Server-side instrumentation for debugging: log payloads forwarded to WebSocket clients
            import logging, json as _json
            logging.getLogger(__name__).info('MonitorConsumer.forward -> payload=%s', payload)
        except Exception:
            pass
        try:
            print('MonitorConsumer.forward -> payload=', payload)
        except Exception:
            pass
        await self.send(text_data=json.dumps(payload))

    @database_sync_to_async
    def _fetch_devices(self):
        if Device:
            return list(Device.objects.all().values("id", "serial_number"))
        return []

    async def _send_initial_status(self):
        devices = await self._fetch_devices()
        # Fetch persisted status if available
        persisted = await self._fetch_status_map()
        for d in devices:
            st = persisted.get(d["id"], {"online": True, "door_state": "CLOSED", "updated_at": None})
            await self.send(text_data=json.dumps({
                "type": "device.status",
                "device_id": d["id"],
                "serial": d.get("serial_number") or str(d["id"]),
                "online": st.get("online", True),
                "door_state": st.get("door_state", "CLOSED"),
                "updated_at": st.get("updated_at")
            }))

    @database_sync_to_async
    def _fetch_status_map(self):
        try:
            from agent.models import DeviceStatus
            # Prefer in-memory/commcenter-known last-seen timestamps recorded during
            # startup broadcasts. This file is written by ModernCommCenter so that
            # freshly connected WebSocket clients receive an up-to-date timestamp
            # even if the DB wasn't updated during CommCenter startup.
            import os, json
            try:
                base = getattr(__import__('django.conf').conf.settings, 'BASE_DIR', os.getcwd())
            except Exception:
                base = os.getcwd()
            rt_file = os.path.join(base, 'zkeco_modern', 'runtime_logs', 'last_status_broadcasts.json')
            broadcasts = {}
            if os.path.exists(rt_file):
                try:
                    with open(rt_file, 'r', encoding='utf-8') as fh:
                        broadcasts = json.load(fh) or {}
                except Exception:
                    broadcasts = {}
            out = {}
            from django.utils.dateparse import parse_datetime
            from django.utils import timezone as dj_tz
            for s in DeviceStatus.objects.select_related("device").all():
                try:
                    db_ts = None
                    if getattr(s, 'updated_at', None) is not None:
                        try:
                            db_ts = s.updated_at
                        except Exception:
                            db_ts = None
                    b = broadcasts.get(str(s.device_id))
                    b_ts = None
                    if b:
                        try:
                            b_ts = parse_datetime(b)
                            # ensure timezone-aware
                            if b_ts is not None and dj_tz.is_naive(b_ts):
                                b_ts = dj_tz.make_aware(b_ts, dj_tz.get_current_timezone())
                        except Exception:
                            b_ts = None

                    # Choose the most recent timestamp between DB and broadcast
                    chosen = None
                    if db_ts and b_ts:
                        try:
                            chosen = db_ts if db_ts >= b_ts else b_ts
                        except Exception:
                            chosen = db_ts or b_ts
                    else:
                        chosen = db_ts or b_ts

                    ua = None
                    if chosen is not None:
                        try:
                            ua = chosen.isoformat() if hasattr(chosen, 'isoformat') else str(chosen)
                        except Exception:
                            ua = str(chosen)
                except Exception:
                    ua = None
                out[s.device_id] = {"online": s.online, "door_state": s.door_state, "updated_at": ua}
            return out
        except Exception:
            return {}

    # Polling removed; relying exclusively on CommCenter broadcasts via channel layer.


class EventsConsumer(AsyncWebsocketConsumer):
    """Live events/alarm stream.

    Clients join the `events` group. Broadcast payload shape:
      {
        "type": "event.log",
        "id": <int>,
        "device_id": <int|None>,
        "content": <str>,
        "classification": <str>,  # e.g. ACCESS_DENIED / FORCED_OPEN / NORMAL
        "alarm": <bool>,
        "created_at": <iso>
      }
    """
    group_name = "events"

    async def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close(); return
        await self.channel_layer.group_add(self.group_name, self.channel_name)  # type: ignore
        await self.accept()

    async def disconnect(self, code):  # pragma: no cover
        await self.channel_layer.group_discard(self.group_name, self.channel_name)  # type: ignore

    async def receive(self, text_data=None, bytes_data=None):  # pragma: no cover
        # No client-originated commands yet
        pass

    async def events_event(self, event):
        payload = event.get("payload", {})
        await self.send(text_data=json.dumps(payload))


class AccessLevelsConsumer(AsyncWebsocketConsumer):
    group_name = "access_levels"

    async def connect(self):
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close(); return
        await self.channel_layer.group_add(self.group_name, self.channel_name)  # type: ignore
        await self.accept()

    async def disconnect(self, code):  # pragma: no cover
        await self.channel_layer.group_discard(self.group_name, self.channel_name)  # type: ignore

    async def receive(self, text_data=None, bytes_data=None):  # pragma: no cover
        pass

    async def access_levels_event(self, event):
        payload = event.get("payload", {})
        await self.send(text_data=json.dumps(payload))
