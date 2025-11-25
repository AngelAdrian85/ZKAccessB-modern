import os
import ctypes
import logging
from typing import Optional, Type

from .modern_comm_center import CommDriver, StubDriver

LOG = logging.getLogger("modern_comm_center.sdk")


class SDKDriverAdapter(StubDriver):
    """ctypes-based SDK adapter scaffold.

    Load order:
      1. Django setting `AGENT_SDK_DLL`
      2. Environment variable `AGENT_SDK_DLL`

    Provide the DLL path via (PowerShell example):
        setx AGENT_SDK_DLL "C:\\Path\\To\\zkaccess.dll"
        (restart shell) or set inside settings.py.

    Extend by adding Python wrappers translating driver protocol methods
    to DLL exports. Keep each wrapper minimal and return dictionaries
    matching the legacy structure (e.g. {"result": int, "data": ...}).
    """

    _loaded = False
    _dll = None

    def __init__(self, dev):
        super().__init__(dev)
        if not SDKDriverAdapter._loaded:
            self._try_load()

    @classmethod
    def _try_load(cls):  # pragma: no cover
        if cls._loaded:
            return
        path = None
        try:
            from django.conf import settings
            path = getattr(settings, "AGENT_SDK_DLL", None)
        except Exception:
            path = None
        path = path or os.getenv("AGENT_SDK_DLL")
        if not path or not os.path.exists(path):
            LOG.warning("SDK DLL not found; set AGENT_SDK_DLL to enable")
            return
        try:
            cls._dll = ctypes.CDLL(path)
            cls._loaded = True
            LOG.info("Loaded SDK DLL: %s", path)
        except Exception as e:
            LOG.error("Failed loading SDK DLL %s: %s", path, e)

    # Example mapping (to be replaced with real signatures):
    # def connect(self):
    #     if self._loaded:
    #         res = self._dll.Connect(...)
    #         return {"result": 1 if res == 0 else -1}
    #     return super().connect()


def get_sdk_adapter_class() -> Optional[Type[CommDriver]]:
    try:
        SDKDriverAdapter._try_load()
        if SDKDriverAdapter._loaded:
            return SDKDriverAdapter
    except Exception:
        pass
    return None
