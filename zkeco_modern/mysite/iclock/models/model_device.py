"""Shim for `mysite.iclock.models.model_device`.

Provides a minimal `Device` class placeholder to satisfy legacy imports
from management commands in test contexts. The class is intentionally
lightweight and only exposes attributes referenced by legacy code where
necessary.
"""

class Device:
    def __init__(self, *args, **kwargs):
        self.sn = kwargs.get('sn')
        self.device_name = kwargs.get('device_name')

    @classmethod
    def objects(cls):
        # Minimal placeholder API; tests typically don't use this directly.
        raise NotImplementedError('model_device.Device.objects is a stub')

__all__ = ['Device']
