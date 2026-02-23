import logging
from typing import Any, Dict

from django.conf import settings

from ..plcommpro_bridge import (
    PlcommproBridgeError,
    PlcommproConnInfo,
    cancel_alarm,
    control_device,
    control_normal_open,
    data_count,
    delete_device_data,
    enable_device,
    get_device_options,
    query_data,
    set_device_data,
    set_device_options,
)

LOG = logging.getLogger("plcommpro_bridge_driver")


class PlcommproBridgeDriver:
    """CommDriver-compatible adapter backed by plcommpro.dll via the 32-bit bridge.

    This is the most reliable integration path on Windows where plcommpro.dll is
    typically 32-bit and cannot be loaded by 64-bit Python.

    Notes:
    - Device `comm_password` is the device communication password (often numeric, default "0").
      It is NOT the HTTPS/web UI login password.
    - Requires env var `ZKACCESS_PYBRIDGE` (or `ZKACCESS_PY32`) pointing to a 32-bit
      Python 3 interpreter.
    """

    def __init__(self, dev):
        self.dev = dev
        self.ip = str(getattr(dev, "ip_address", "") or "")
        self.port = int(getattr(dev, "port", 4370) or 4370)
        self.password = str(getattr(dev, "comm_password", "") or "")
        if not self.password:
            try:
                self.password = str(getattr(settings, 'ZKACCESS_DEFAULT_COMM_PASSWORD', '') or '').strip()
            except Exception:
                self.password = self.password
        self.timeout_ms = 5000

    def _conn(self) -> PlcommproConnInfo:
        return PlcommproConnInfo(
            ipaddress=self.ip,
            ip_port=self.port,
            password=self.password,
            timeout=int(self.timeout_ms),
        )

    def connect(self) -> Dict[str, Any]:
        try:
            # A cheap connect validation: ask for a minimal option.
            resp = get_device_options(self._conn(), "IPAddress")
            if resp.get("ok"):
                return {"result": 1, "data": resp.get("data", "")}
            return {
                "result": -1,
                "error": f"plcommpro_connect_failed result={resp.get('result')} last_error={resp.get('last_error')} data={resp.get('data')}",
            }
        except PlcommproBridgeError as e:
            return {"result": -1, "error": str(e)}
        except Exception as e:
            LOG.exception("connect failed")
            return {"result": -1, "error": str(e)}

    def disconnect(self) -> Dict[str, Any]:
        # Bridge is request/response; each call connects/disconnects internally.
        return {"result": 1}

    def get_options(self) -> Dict[str, Any]:
        try:
            resp = get_device_options(self._conn(), "IPAddress,NetMask,GATEIPAddress")
            if resp.get("ok"):
                return {"result": resp.get("result", 0), "data": resp.get("data", "")}
            return {"result": -1, "error": resp.get("data") or "get_options_failed"}
        except Exception as e:
            return {"result": -1, "error": str(e)}

    def set_options(self, items: str) -> Dict[str, Any]:
        try:
            resp = set_device_options(self._conn(), items)
            if resp.get("ok"):
                return {"result": resp.get("result", 0), "data": resp.get("data", "")}
            return {"result": -1, "error": resp.get("data") or "set_options_failed"}
        except Exception as e:
            return {"result": -1, "error": str(e)}

    def get_rtlog(self) -> Dict[str, Any]:
        try:
            # Legacy CommCenter primarily used transaction NewRecord for near-realtime.
            # Keep this lightweight to avoid re-downloading full logs each poll.
            resp_nr = query_data(self._conn(), table="transaction", fields="*", option="NewRecord")
            if resp_nr.get("ok"):
                data_nr = resp_nr.get("data") or ""
                return {"result": 0 if data_nr == "" else 1, "data": data_nr}

            # Some SDK bundles expose a dedicated rtlog table.
            resp = query_data(self._conn(), table="rtlog", fields="*")
            if resp.get("ok"):
                data = resp.get("data") or ""
                return {"result": 0 if data == "" else 1, "data": data}

            # Fallback to transaction table (full) as last resort.
            resp2 = query_data(self._conn(), table="transaction", fields="*")
            if resp2.get("ok"):
                data2 = resp2.get("data") or ""
                return {"result": 0 if data2 == "" else 1, "data": data2}

            return {
                "result": -1,
                "error": f"rtlog_failed result={resp.get('result')} last_error={resp.get('last_error')} data={resp.get('data')}",
            }
        except Exception as e:
            return {"result": -1, "error": str(e)}

    def get_transaction(self, newlog: bool = False) -> Dict[str, Any]:
        try:
            # Match legacy behavior: use NewRecord when requested.
            resp = query_data(
                self._conn(),
                table="transaction",
                fields="*",
                option=("NewRecord" if newlog else ""),
            )
            if not resp.get("ok"):
                return {"result": -1, "error": resp.get("data") or "transaction_failed"}

            raw = resp.get("data") or ""
            lines = [ln for ln in raw.split("\r\n") if ln]
            data = {i + 1: ln for i, ln in enumerate(lines)}
            return {"result": len(lines), "data": data}
        except Exception as e:
            return {"result": -1, "error": str(e)}

    def query_data(self, table: str, fields: str = "*", filter: str = "", option: str = "") -> Dict[str, Any]:
        try:
            resp = query_data(self._conn(), table=table, fields=fields, filter=filter, option=option)
            if resp.get("ok"):
                return {"result": resp.get("result", 0), "data": resp.get("data", "")}
            return {"result": -1, "error": resp.get("data") or "query_failed"}
        except Exception as e:
            return {"result": -1, "error": str(e)}

    def delete_data(self, table: str, filter: str = "") -> Dict[str, Any]:
        try:
            resp = delete_device_data(self._conn(), table=table, filter=filter)
            if resp.get("ok"):
                return {"result": resp.get("result", 0), "data": resp.get("data", "")}
            return {"result": -1, "error": resp.get("data") or "delete_failed"}
        except Exception as e:
            return {"result": -1, "error": str(e)}

    def update_data(self, *args, **kwargs) -> Dict[str, Any]:
        try:
            # Signature follows legacy: update_data(table, data, extra/options)
            table = str(args[0] if len(args) >= 1 else kwargs.get('table') or '').strip()
            data = str(args[1] if len(args) >= 2 else kwargs.get('data') or '')
            extra = str(args[2] if len(args) >= 3 else kwargs.get('extra') or kwargs.get('option') or '').strip()
            if not table:
                return {"result": -1, "error": "missing_table"}

            # Some panels require a temporary disable while writing user tables.
            # Best-effort: ignore failures and still attempt the write.
            disable_during = table.strip().lower() in ("user",)
            if disable_during:
                try:
                    enable_device(self._conn(), 0)
                except Exception:
                    pass
            resp = set_device_data(self._conn(), table=table, data=data, option=extra)
            if disable_during:
                try:
                    enable_device(self._conn(), 1)
                except Exception:
                    pass
            if resp.get("ok"):
                return {"result": resp.get("result", 0), "data": resp.get("data", "")}
            return {
                "result": -1,
                "error": resp.get("data")
                or f"set_data_failed result={resp.get('result')} last_error={resp.get('last_error')}",
            }
        except PlcommproBridgeError as e:
            return {"result": -1, "error": str(e)}
        except Exception as e:
            return {"result": -1, "error": str(e)}

    def Get_Data_Count(self, table: str) -> Dict[str, Any]:
        try:
            resp = data_count(self._conn(), table=table)
            if resp.get("ok"):
                return {"result": resp.get("result", 0)}
            return {"result": -1, "error": resp.get("data") or "count_failed"}
        except Exception as e:
            return {"result": -1, "error": str(e)}

    def enable_device(self, enable: int) -> Dict[str, Any]:
        try:
            resp = enable_device(self._conn(), int(enable))
            if resp.get("ok"):
                return {"result": resp.get("result", 0)}
            return {"result": -1, "error": resp.get("data") or "enable_device_failed"}
        except Exception as e:
            return {"result": -1, "error": str(e)}

    def controldevice(self, door: int, index: int, state: int) -> Dict[str, Any]:
        try:
            resp = control_device(self._conn(), int(door or 0), int(index or 0), int(state or 0), time=0)
            if resp.get("ok"):
                return {"result": 1, "data": ""}
            return {
                "result": -1,
                "error": (
                    f"controldevice_failed result={resp.get('result')} last_error={resp.get('last_error')} "
                    f"dll={resp.get('dll_path_used')}"
                ),
            }
        except Exception as e:
            return {"result": -1, "error": str(e)}

    def cancel_alarm(self, door: int | str | None = None) -> Dict[str, Any]:
        try:
            door_int = 0
            try:
                if door is not None and str(door).strip() != '':
                    door_int = int(str(door).strip())
            except Exception:
                door_int = 0
            resp = cancel_alarm(self._conn(), door=door_int)
            if resp.get("ok"):
                return {"result": 1, "data": ""}
            return {
                "result": -1,
                "error": (
                    f"cancel_alarm_failed result={resp.get('result')} last_error={resp.get('last_error')} "
                    f"dll={resp.get('dll_path_used')}"
                ),
            }
        except Exception as e:
            return {"result": -1, "error": str(e)}

    def control_normal_open(self, door: int, state: int) -> Dict[str, Any]:
        try:
            resp = control_normal_open(self._conn(), int(door or 0), int(state or 0))
            if resp.get("ok"):
                return {"result": 1, "data": ""}
            return {
                "result": -1,
                "error": (
                    f"normal_open_failed result={resp.get('result')} last_error={resp.get('last_error')} "
                    f"dll={resp.get('dll_path_used')}"
                ),
            }
        except Exception as e:
            return {"result": -1, "error": str(e)}
