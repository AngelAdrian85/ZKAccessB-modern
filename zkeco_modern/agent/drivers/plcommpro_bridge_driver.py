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
    get_rtlog as bridge_get_rtlog,
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
        self._resolved_password = None
        self.timeout_ms = 5000

    def _conn(self, password_override: str | None = None) -> PlcommproConnInfo:
        pw = self.password
        if password_override is not None:
            pw = str(password_override)
        elif self._resolved_password is not None:
            pw = str(self._resolved_password)
        return PlcommproConnInfo(
            ipaddress=self.ip,
            ip_port=self.port,
            password=pw,
            timeout=int(self.timeout_ms),
        )

    def _password_candidates(self):
        vals = []
        if self._resolved_password is not None:
            vals.append(str(self._resolved_password))
        vals.append(str(self.password or ''))
        try:
            vals.append(str(getattr(settings, 'ZKACCESS_DEFAULT_COMM_PASSWORD', '') or '').strip())
        except Exception:
            pass
        vals.extend(['0', ''])
        seen = set()
        out = []
        for v in vals:
            if v in seen:
                continue
            seen.add(v)
            out.append(v)
        return out

    def _with_password_fallback(self, fn):
        last = {"ok": False, "result": -1, "data": "connect failed"}
        for pw in self._password_candidates():
            try:
                resp = fn(self._conn(pw))
                if isinstance(resp, dict) and resp.get('ok'):
                    self._resolved_password = pw
                    self.password = pw
                    return resp
                if isinstance(resp, dict):
                    last = resp
            except Exception as e:
                last = {"ok": False, "result": -1, "data": str(e)}
        return last

    def connect(self) -> Dict[str, Any]:
        try:
            # A cheap connect validation: ask for a minimal option.
            resp = self._with_password_fallback(lambda c: get_device_options(c, "IPAddress"))
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

    def get_options(self, items: str = "") -> Dict[str, Any]:
        try:
            items = (items or "").strip() or "IPAddress,NetMask,GATEIPAddress"
            resp = get_device_options(self._conn(), items)
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
        """Retrieve real-time log entries.

        Priority:
        1. GetRTLog() DLL function (returns raw Wiegand card numbers including
           for unregistered / access-denied cards - the only reliable way to get
           the actual card number from many ZKTeco panel firmwares).
        2. GetDeviceData(transaction, NewRecord) - fallback for firmwares that
           don't support GetRTLog or panels that buffer events there only.
        3. GetDeviceData(rtlog, *) - legacy table fallback.
        """
        # Priority 1 is in its own try so exceptions fall through to 2/3.
        # IMPORTANT: some firmwares return OK from GetRTLog() but provide no
        # events even though transaction NewRecord has data. In that case we
        # must fall back to priority 2 instead of returning early.
        try:
            resp_rtlog = self._with_password_fallback(lambda c: bridge_get_rtlog(c))
            if resp_rtlog.get("ok"):
                data_rtlog = resp_rtlog.get("data") or ""
                # Filter out header-only responses
                lines_rtlog = [
                    ln
                    for ln in data_rtlog.split("\r\n")
                    if ln.strip() and not ln.strip().lower().startswith("pin,")
                ]
                if lines_rtlog:
                    LOG.debug("get_rtlog via GetRTLog: %d lines", len(lines_rtlog))
                    return {"result": len(lines_rtlog), "data": data_rtlog}
        except Exception as exc:
            LOG.debug("GetRTLog DLL call failed, falling back to transaction: %s", exc)

        # Priority 2 & 3 fallback.
        try:
            # Priority 2: transaction NewRecord (consumed-once queue).
            # IMPORTANT: avoid fields='*' here.
            # With fields='*' many firmwares return tab-separated key=value pairs
            # (e.g. "Cardno=...\tPin=..."), which CommCenter won't parse as a
            # rtlog/transaction CSV line. Request explicit fields so the output
            # is value-only and stable in position.
            # Include Index when available so repeated scans within the same second
            # don't collapse into identical raw lines (many firmwares are only
            # second-resolution on Time_second).
            txn_fields = "Cardno,Pin,Verified,DoorID,EventType,InOutState,Time_second,Index"
            resp_nr = self._with_password_fallback(
                lambda c: query_data(c, table="transaction", fields=txn_fields, option="NewRecord")
            )
            if resp_nr.get("ok"):
                data_nr = resp_nr.get("data") or ""
                # Filter out header-only responses (some devices return a header line)
                raw_lines = [
                    ln
                    for ln in data_nr.split("\r\n")
                    if ln.strip() and not ln.strip().lower().replace(' ', '').startswith("cardno,")
                ]

                # CommCenter/UI expects RTLOG-like line shapes:
                # - Format A: ts,pin,card,door,code,verify,...
                # - Format B: pin,verified,door,eventType,inOut,time_second[,index],cardno,sitecode
                # The transaction table explicit field list yields a Cardno-first line.
                # Re-shape it into a pin-first RTLOG Format B line so downstream parsing
                # finds CardNo at the expected position and can dedupe using Index.
                lines_nr: list[str] = []
                for ln in raw_lines:
                    normalized = ln
                    if "\t" in normalized and "," not in normalized:
                        normalized = normalized.replace("\t", ",")
                    if ";" in normalized and "," not in normalized and normalized.count(';') >= 2:
                        normalized = normalized.replace(";", ",")
                    parts = [p.strip() for p in normalized.split(',')]
                    if len(parts) == 8:
                        cardno, pin, verified, door, event_type, in_out, time_second, idx = parts
                        # 9-field RTLOG Format B: pin,verified,door,eventType,inOut,time_second,index,cardno,sitecode
                        ln = f"{pin},{verified},{door},{event_type},{in_out},{time_second},{idx},{cardno},0"
                    elif len(parts) == 7:
                        # Back-compat: some devices ignore Index even when requested.
                        cardno, pin, verified, door, event_type, in_out, time_second = parts
                        ln = f"{pin},{verified},{door},{event_type},{in_out},{time_second},{cardno},0"
                    lines_nr.append(ln)

                return {"result": len(lines_nr), "data": "\r\n".join(lines_nr) + ("\r\n" if lines_nr else "")}

            # Some firmwares reject multi-field selection for transaction table (returns -114)
            # but succeed with fields='*' and a key=value payload. Retry once and normalize.
            resp_nr_star = self._with_password_fallback(
                lambda c: query_data(c, table="transaction", fields="*", option="NewRecord")
            )
            if resp_nr_star.get("ok"):
                data_star = resp_nr_star.get("data") or ""
                raw_lines_star = [
                    ln
                    for ln in data_star.split("\r\n")
                    if ln.strip() and not ln.strip().lower().replace(' ', '').startswith("cardno,")
                ]

                def _kv_to_csv8(line: str) -> str:
                    line = (line or '').strip()
                    if not line:
                        return ''
                    # Typical wildcard transaction shape: "Cardno=...\tPin=...\t..."
                    if '=' not in line:
                        return line
                    sep = "\t" if "\t" in line else ","
                    items = [p.strip() for p in line.split(sep) if p.strip()]
                    kv: dict[str, str] = {}
                    for it in items:
                        if '=' not in it:
                            continue
                        k, v = it.split('=', 1)
                        kv[str(k or '').strip().lower()] = str(v or '').strip()
                    cardno = kv.get('cardno', '')
                    pin = kv.get('pin', '')
                    verified = kv.get('verified', '')
                    door = kv.get('doorid', kv.get('door', ''))
                    event_type = kv.get('eventtype', kv.get('event', ''))
                    in_out = kv.get('inoutstate', kv.get('inout', ''))
                    time_second = kv.get('time_second', kv.get('timesecond', kv.get('time', '')))
                    idx = kv.get('index', kv.get('id', kv.get('logid', '')))
                    # Return 8-field Cardno-first CSV like explicit field list.
                    if any([cardno, pin, verified, door, event_type, in_out, time_second, idx]):
                        return f"{cardno},{pin},{verified},{door},{event_type},{in_out},{time_second},{idx}"
                    return line

                lines_nr2: list[str] = []
                for ln in raw_lines_star:
                    normalized = _kv_to_csv8(ln)
                    if "\t" in normalized and "," not in normalized:
                        normalized = normalized.replace("\t", ",")
                    if ";" in normalized and "," not in normalized and normalized.count(';') >= 2:
                        normalized = normalized.replace(";", ",")
                    parts = [p.strip() for p in normalized.split(',')]
                    if len(parts) == 8:
                        cardno, pin, verified, door, event_type, in_out, time_second, idx = parts
                        normalized = f"{pin},{verified},{door},{event_type},{in_out},{time_second},{idx},{cardno},0"
                    elif len(parts) == 7:
                        cardno, pin, verified, door, event_type, in_out, time_second = parts
                        normalized = f"{pin},{verified},{door},{event_type},{in_out},{time_second},{cardno},0"
                    lines_nr2.append(normalized)

                return {"result": len(lines_nr2), "data": "\r\n".join(lines_nr2) + ("\r\n" if lines_nr2 else "")}

            # Priority 3: dedicated rtlog table (some SDK bundles).
            # Try to request a pin-first 8-field variant so CommCenter detects it
            # as RTLOG format B (not the 7-field transaction format).
            rtlog_fields = "Pin,Verified,DoorID,EventType,InOutState,Time_second,Cardno,Sitecode"
            resp = self._with_password_fallback(
                lambda c: query_data(c, table="rtlog", fields=rtlog_fields)
            )
            if (not resp.get("ok")):
                resp = self._with_password_fallback(lambda c: query_data(c, table="rtlog", fields="*"))
            if resp.get("ok"):
                data = resp.get("data") or ""
                lines = [ln for ln in data.split("\r\n") if ln.strip() and not ln.strip().lower().startswith("pin,")]
                return {"result": len(lines), "data": "\r\n".join(lines) + ("\r\n" if lines else "")}

            return {
                "result": -1,
                "error": f"rtlog_failed result={resp_nr.get('result')} last_error={resp_nr.get('last_error')}",
            }
        except Exception as e:
            return {"result": -1, "error": str(e)}

    def get_transaction(self, newlog: bool = False) -> Dict[str, Any]:
        try:
            # SDK-documented field order for transaction table:
            # Cardno,Pin,Verified,DoorID,EventType,InOutState,Time_second[,Index]
            # Using explicit field list guarantees Cardno is at position 0
            # even for unregistered card scans on C3/F3/G series panels.
            # Include Index when available so repeated scans in the same second
            # don't collapse into identical raw lines.
            def _query_txn(fields: str) -> Dict[str, Any]:
                return self._with_password_fallback(
                    lambda c: query_data(
                        c,
                        table="transaction",
                        fields=fields,
                        option=("NewRecord" if newlog else ""),
                    )
                )

            TXN_FIELDS = "Cardno,Pin,Verified,DoorID,EventType,InOutState,Time_second,Index"
            used_star = False
            resp = _query_txn(TXN_FIELDS)
            if not resp.get("ok"):
                # Fallback to wildcard if explicit fields not supported
                resp = _query_txn("*")
                used_star = True
            if not resp.get("ok"):
                return {"result": -1, "error": resp.get("data") or "transaction_failed"}

            raw = resp.get("data") or ""
            raw_lines = [ln for ln in raw.split("\r\n") if ln and ln.strip()]
            # Some devices include a CSV header
            raw_lines = [
                ln
                for ln in raw_lines
                if not ln.strip().lower().replace(' ', '').startswith('cardno,')
            ]

            # If the explicit Cardno field appears consistently empty while other
            # columns are populated, retry once with CardNo (some bundles/firmwares
            # are picky about field casing).
            if (not used_star) and raw_lines:
                try:
                    # Only applies to the explicit-field selection (not wildcard key=value).
                    if TXN_FIELDS.lower().startswith("cardno,") and '=' not in raw:
                        empties = 0
                        populated = 0
                        for ln in raw_lines[:20]:
                            normalized = ln
                            if "\t" in normalized and "," not in normalized:
                                normalized = normalized.replace("\t", ",")
                            parts = [p.strip() for p in str(normalized or '').split(',')]
                            if len(parts) >= 2 and any(parts[1:]):
                                populated += 1
                                if not (parts[0] or '').strip():
                                    empties += 1
                        if populated and empties == populated:
                            resp2 = _query_txn(
                                "CardNo,Pin,Verified,DoorID,EventType,InOutState,Time_second,Index"
                            )
                            if resp2.get("ok"):
                                raw = resp2.get("data") or ""
                                raw_lines = [ln for ln in raw.split("\r\n") if ln and ln.strip()]
                                raw_lines = [
                                    ln
                                    for ln in raw_lines
                                    if not ln.strip().lower().replace(' ', '').startswith('cardno,')
                                ]
                except Exception:
                    pass

            def _kv_to_parts(line: str) -> tuple[str, str, str, str, str, str, str, str]:
                """Return (cardno,pin,verified,door,event_type,in_out,time_second,idx)."""
                line = (line or '').strip()
                if not line:
                    return ('', '', '', '', '', '', '', '')
                if '=' not in line:
                    return ('', '', '', '', '', '', '', '')
                sep = "\t" if "\t" in line else ","
                items = [p.strip() for p in line.split(sep) if p.strip()]
                kv: dict[str, str] = {}
                for it in items:
                    if '=' not in it:
                        continue
                    k, v = it.split('=', 1)
                    kv[str(k or '').strip().lower()] = str(v or '').strip()
                cardno = kv.get('cardno', '')
                pin = kv.get('pin', '')
                verified = kv.get('verified', '')
                door = kv.get('doorid', kv.get('door', ''))
                event_type = kv.get('eventtype', kv.get('event', ''))
                in_out = kv.get('inoutstate', kv.get('inout', ''))
                time_second = kv.get('time_second', kv.get('timesecond', kv.get('time', '')))
                idx = kv.get('index', kv.get('id', kv.get('logid', '')))
                return (cardno, pin, verified, door, event_type, in_out, time_second, idx)

            normalized_lines: list[str] = []
            for ln in raw_lines:
                normalized = ln
                if "\t" in normalized and "," not in normalized:
                    normalized = normalized.replace("\t", ",")
                if ";" in normalized and "," not in normalized and normalized.count(';') >= 2:
                    normalized = normalized.replace(";", ",")

                # Wildcard key=value payload
                if '=' in normalized:
                    cardno, pin, verified, door, event_type, in_out, time_second, idx = _kv_to_parts(normalized)
                    if any([cardno, pin, verified, door, event_type, in_out, time_second, idx]):
                        normalized_lines.append(
                            f"{pin},{verified},{door},{event_type},{in_out},{time_second},{idx},{cardno},0"
                        )
                    else:
                        normalized_lines.append(ln)
                    continue

                parts = [p.strip() for p in normalized.split(',')]
                if len(parts) == 8:
                    cardno, pin, verified, door, event_type, in_out, time_second, idx = parts
                    normalized_lines.append(
                        f"{pin},{verified},{door},{event_type},{in_out},{time_second},{idx},{cardno},0"
                    )
                elif len(parts) == 7:
                    # Back-compat: device ignored Index
                    cardno, pin, verified, door, event_type, in_out, time_second = parts
                    normalized_lines.append(
                        f"{pin},{verified},{door},{event_type},{in_out},{time_second},{cardno},0"
                    )
                else:
                    normalized_lines.append(ln)

            data = {i + 1: ln for i, ln in enumerate(normalized_lines)}
            return {"result": len(normalized_lines), "data": data}
        except Exception as e:
            return {"result": -1, "error": str(e)}

    def get_panel_user_card_map(self) -> Dict[str, str]:
        """Download the panel's user table and return a PIN→CardNo mapping.

        ZKTeco C3 stores the enrolled Wiegand card number in the 'user' table
        under the field 'CardNo' (some firmware variants use 'ViceCard').
        Querying the table directly gives us the real card number that the panel
        saw during the scan — something *not* transmitted in GetRTLog rtlog lines.
        Returns {pin_str: card_no_str} or {} on error.
        """
        mapping: Dict[str, str] = {}
        # Try CardNo first (most C3/F3/G series), then ViceCard (older bundles)
        for card_field in ('CardNo', 'ViceCard', 'Cardno'):
            try:
                resp = self.query_data(table='user', fields=f'Pin,{card_field}')
                raw = (resp.get('data') or '').strip()
                if not raw or resp.get('result', -1) < 0:
                    continue
                lines = [ln for ln in raw.replace('\r\n', '\n').replace('\r', '\n').split('\n') if ln.strip()]
                if not lines:
                    continue
                # First line may be a CSV header; detect it
                first = lines[0].lower().replace(' ', '')
                start = 1 if 'pin' in first and ('cardno' in first or 'vicecard' in first) else 0
                parsed = 0
                for line in lines[start:]:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 2:
                        pin_v = parts[0].strip()
                        card_v = parts[1].strip()
                        if pin_v and card_v and card_v not in ('', '0', '00000000'):
                            mapping[pin_v] = card_v
                            parsed += 1
                if parsed > 0:
                    LOG.info('panel_user_card_map: %d entries via %s', parsed, card_field)
                    return mapping
            except Exception as exc:
                LOG.debug('get_panel_user_card_map field=%s err=%s', card_field, exc)
        return mapping

    def query_data(self, table: str, fields: str = "*", filter: str = "", option: str = "") -> Dict[str, Any]:
        try:
            resp = self._with_password_fallback(
                lambda c: query_data(c, table=table, fields=fields, filter=filter, option=option)
            )
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
