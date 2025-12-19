from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging


logger = logging.getLogger(__name__)


def broadcast_device_status(device_id: int, online: bool, door_state: str = None, serial: str = None, updated_at: str = None):
    """Broadcast a device.status payload to the `monitor` channel group.

    Payload keys mirror MonitorConsumer initial payload: type, device_id, serial, online, door_state
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        payload = {
            'type': 'device.status',
            'device_id': int(device_id),
            'serial': serial,
            'online': bool(online),
            'door_state': door_state,
            'updated_at': updated_at,
        }
        try:
            logger.info('broadcast_device_status -> group_send monitor payload=%s', payload)
        except Exception:
            # Best-effort logging; ignore failures to avoid breaking hot path
            pass
        # Rely on structured logging above; remove noisy stdout fallback
        async_to_sync(channel_layer.group_send)('monitor', {'type': 'monitor_event', 'payload': payload})
    except Exception:
        # Avoid raising in hot code paths
        pass
