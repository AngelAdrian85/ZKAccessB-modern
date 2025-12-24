from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging
import inspect


logger = logging.getLogger(__name__)


def _caller_origin():
    try:
        stk = inspect.stack()
        # 0=current frame, 1=caller
        if len(stk) > 2:
            frame = stk[2]
        elif len(stk) > 1:
            frame = stk[1]
        else:
            return None
        module = inspect.getmodule(frame[0])
        modname = module.__name__ if module else None
        func = frame.function if hasattr(frame, 'function') else None
        return f"{modname}.{func}" if modname and func else (modname or func)
    except Exception:
        return None


def broadcast_device_status(device_id: int, online: bool, door_state: str = None, serial: str = None, updated_at: str = None):
    """Broadcast a device.status payload to the `monitor` channel group.

    Payload keys mirror MonitorConsumer initial payload: type, device_id, serial, online, door_state
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        origin = _caller_origin()
        payload = {
            'type': 'device.status',
            'device_id': int(device_id),
            'serial': serial,
            'online': bool(online),
            'door_state': door_state,
            'updated_at': updated_at,
            'origin': origin,
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
