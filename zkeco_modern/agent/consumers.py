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
            st = persisted.get(d["id"], {"online": True, "door_state": "CLOSED"})
            await self.send(text_data=json.dumps({
                "type": "device.status",
                "device_id": d["id"],
                "serial": d.get("serial_number") or str(d["id"]),
                "online": st.get("online", True),
                "door_state": st.get("door_state", "CLOSED")
            }))

    @database_sync_to_async
    def _fetch_status_map(self):
        try:
            from agent.models import DeviceStatus
            return {s.device_id: {"online": s.online, "door_state": s.door_state} for s in DeviceStatus.objects.select_related("device").all()}
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
