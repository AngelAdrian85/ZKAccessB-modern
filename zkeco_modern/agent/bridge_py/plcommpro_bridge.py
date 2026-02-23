# -*- coding: utf-8 -*-
"""Python 3.x (32-bit) bridge for ZKTeco plcommpro.dll.

This script is executed by a 32-bit Python 3 interpreter. It performs one
request (op) per invocation and prints a single JSON object to stdout.

Why this exists:
- plcommpro.dll in typical ZKAccessB installs is 32-bit.
- The modern server runs on 64-bit Python 3 and cannot load 32-bit DLLs.
- We keep the main app fully modern, and isolate SDK calls in this bridge.

Request format (JSON, passed via --request):
{
    "action": "get_options"|"set_options"|"query_data"|"data_count"|"delete_data"|"set_data"|"search_device"|"modify_ip"|"control_device"|"cancel_alarm"|"reboot"|"control_normal_open",
  "dll_path": "C:\\Windows\\SysWOW64\\plcommpro.dll" (optional),
  "comminfo": {
    "comm_type": 1,
    "ipaddress": "192.168.1.220",
    "ip_port": 4370,
    "password": "0",
    "timeout": 3000
  },
  ... action-specific fields ...
}

Response format:
{
  "ok": true|false,
  "result": <int>,
  "data": <string>,
  "last_error": <int>
}
"""

from __future__ import annotations

import json
import sys
from ctypes import create_string_buffer, windll


def _b(s: object) -> bytes:
    if s is None:
        return b""
    if isinstance(s, (bytes, bytearray)):
        return bytes(s)
    return str(s).encode("utf-8", "ignore")


def _pull_last_error(dll) -> int:
    try:
        return int(dll.PullLastError())
    except Exception:
        return 0


def _load_dll(dll_path: str | None):
    if dll_path:
        return windll.LoadLibrary(dll_path)
    return windll.LoadLibrary("plcommpro.dll")


def _connect(dll, comminfo: dict) -> int:
    comm_type = int(comminfo.get("comm_type", 1) or 1)
    protocol_override = str(comminfo.get("protocol") or "").strip()
    ip = str(comminfo.get("ipaddress", "") or "")
    port = int(comminfo.get("ip_port", 4370) or 4370)
    passwd = str(comminfo.get("password", "") or "")
    timeout = int(comminfo.get("timeout", 3000) or 3000)

    if comm_type == 1:
        proto = protocol_override or "TCP"
        params = f"protocol={proto},ipaddress={ip},port={port},timeout={timeout}"
        if passwd.strip():
            params += f",passwd={passwd}"
            # Newer panels / SDKs may require commKey for encrypted communication.
            # Keep passwd for backward compatibility; sending both is safe.
            params += f",commKey={passwd}"
    else:
        # RS485 not implemented in this bridge.
        com_port = str(comminfo.get("com_port", "COM1") or "COM1")
        baudrate = str(comminfo.get("baudrate", "9600") or "9600")
        com_address = int(comminfo.get("com_address", 1) or 1)
        params = f"protocol=RS485,port={com_port},baudrate={baudrate}bps,deviceid={com_address},timeout={timeout}"
        if passwd.strip():
            params += f",passwd={passwd}"

    constr = create_string_buffer(_b(params))
    h = int(dll.Connect(constr))
    if h > 0:
        return h

    err = _pull_last_error(dll)
    if err > 0:
        err = -err
    return int(err or -1)


def _disconnect(dll, handle: int) -> None:
    try:
        if int(handle) > 0:
            dll.Disconnect(int(handle))
    except Exception:
        pass


def _ok(result: int, data: str = "", last_error: int = 0) -> dict:
    return {"ok": True, "result": int(result), "data": data, "last_error": int(last_error)}


def _fail(result: int, data: str = "", last_error: int = 0) -> dict:
    return {"ok": False, "result": int(result), "data": data, "last_error": int(last_error)}


def main(argv: list[str]) -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--request", default="")
    ns = ap.parse_args(argv)

    if not ns.request:
        sys.stdout.write(json.dumps(_fail(-1, "missing --request")))
        return 2

    try:
        req = json.loads(ns.request)
    except Exception as e:
        sys.stdout.write(json.dumps(_fail(-1, f"invalid json: {e}")))
        return 2

    action = str(req.get("action") or "").strip().lower()
    comminfo = req.get("comminfo") or {}
    dll_path = req.get("dll_path")

    try:
        dll = _load_dll(dll_path)
    except Exception as e:
        sys.stdout.write(json.dumps(_fail(-2, f"dll load failed: {e}")))
        return 2

    handle = 0
    try:
        # UDP operations don't use a connected handle.
        if action == "search_device":
            address = str(req.get("address") or "255.255.255.255")
            dev_buf = create_string_buffer(b"", 65536)
            ret = int(dll.SearchDevice(_b("UDP"), _b(address), dev_buf))
            last_error = _pull_last_error(dll)
            data = ""
            if ret >= 0:
                raw = bytes(dev_buf.raw).split(b"\x00", 1)[0]
                data = raw.decode("latin-1", "ignore")
            sys.stdout.write(json.dumps({"ok": ret >= 0, "result": ret, "data": data, "last_error": last_error}))
            return 0

        if action == "modify_ip":
            address = str(req.get("address") or "255.255.255.255")
            payload = str(req.get("payload") or "")
            pbuffer = create_string_buffer(_b(payload))
            ret = int(dll.ModifyIPAddress(_b("UDP"), _b(address), pbuffer))
            last_error = _pull_last_error(dll)
            sys.stdout.write(json.dumps({"ok": ret >= 0, "result": ret, "data": "", "last_error": last_error}))
            return 0

        # TCP/RS485 actions: connect first
        handle = _connect(dll, comminfo)
        if int(handle) <= 0:
            last_error = _pull_last_error(dll)
            sys.stdout.write(json.dumps(_fail(int(handle), "connect failed", last_error)))
            return 0

        if action == "get_options":
            items = str(req.get("items") or "").strip()
            op_buf = create_string_buffer(b"", 2048)
            pitems = create_string_buffer(_b(items))
            ret = int(dll.GetDeviceParam(int(handle), op_buf, 2048, pitems))
            last_error = _pull_last_error(dll)
            data = ""
            if ret >= 0:
                raw = bytes(op_buf.raw).split(b"\x00", 1)[0]
                data = raw.decode("latin-1", "ignore")
            sys.stdout.write(json.dumps({"ok": ret >= 0, "result": ret, "data": data, "last_error": last_error}))
            return 0

        if action == "set_options":
            items = str(req.get("items") or "").strip()
            pitems = create_string_buffer(_b(items))
            ret = int(dll.SetDeviceParam(int(handle), pitems))
            last_error = _pull_last_error(dll)
            sys.stdout.write(json.dumps({"ok": ret >= 0, "result": ret, "data": "", "last_error": last_error}))
            return 0

        if action == "data_count":
            table = str(req.get("table") or "").strip()
            ret = int(dll.GetDeviceDataCount(int(handle), _b(table), _b(""), _b("")))
            last_error = _pull_last_error(dll)
            sys.stdout.write(json.dumps({"ok": ret >= 0, "result": ret, "data": "", "last_error": last_error}))
            return 0

        if action == "query_data":
            table = str(req.get("table") or "").strip()
            fields = str(req.get("fields") or "*").strip()
            flt = str(req.get("filter") or "").strip()
            opt = str(req.get("option") or "").strip()
            buf_len = int(req.get("buffer_len") or 2097152)

            str_buf = create_string_buffer(b"", buf_len)
            ret = int(
                dll.GetDeviceData(
                    int(handle),
                    str_buf,
                    int(buf_len),
                    create_string_buffer(_b(table)),
                    create_string_buffer(_b(fields)),
                    create_string_buffer(_b(flt)),
                    create_string_buffer(_b(opt)),
                )
            )
            last_error = _pull_last_error(dll)
            data = ""
            if ret >= 0:
                raw = bytes(str_buf.raw).split(b"\x00", 1)[0]
                data = raw.decode("latin-1", "ignore")
            sys.stdout.write(json.dumps({"ok": ret >= 0, "result": ret, "data": data, "last_error": last_error}))
            return 0

        if action == "delete_data":
            table = str(req.get("table") or "").strip()
            flt = str(req.get("filter") or "").strip()
            ptable = create_string_buffer(_b(table))
            pfilter = create_string_buffer(_b(flt))
            popt = create_string_buffer(b"")
            ret = int(dll.DeleteDeviceData(int(handle), ptable, pfilter, popt))
            last_error = _pull_last_error(dll)
            sys.stdout.write(json.dumps({"ok": ret >= 0, "result": ret, "data": "", "last_error": last_error}))
            return 0

        if action == "set_data":
            table = str(req.get("table") or "").strip()
            data = str(req.get("data") or "")
            opt = str(req.get("option") or "").strip()
            ptable = create_string_buffer(_b(table))
            pdata = create_string_buffer(_b(data))
            popt = create_string_buffer(_b(opt))
            ret = int(dll.SetDeviceData(int(handle), ptable, pdata, popt))
            last_error = _pull_last_error(dll)
            sys.stdout.write(json.dumps({"ok": ret >= 0, "result": ret, "data": "", "last_error": last_error}))
            return 0

        if action == "enable_device":
            # Many panels require temporary disable during user-table writes.
            enable = int(req.get("enable") or 0)
            try:
                ret = int(dll.EnableDevice(int(handle), int(enable)))
            except Exception:
                # Some SDK bundles expose this as DisableDevice/EnableDevice with a different signature.
                # Keep a stable error shape.
                ret = -1
            last_error = _pull_last_error(dll)
            sys.stdout.write(json.dumps({"ok": ret >= 0, "result": ret, "data": "", "last_error": last_error}))
            return 0

        if action in {"control_device", "cancel_alarm", "reboot", "control_normal_open"}:
            door = int(req.get("door") or 0)
            index = int(req.get("index") or 0)
            state = int(req.get("state") or 0)
            time = int(req.get("time") or 0)
            reserved = create_string_buffer(_b(req.get("reserved") or ""))

            # Legacy semantics (see debug_pyc/devcomm.py):
            # - control_device: ControlDevice(handle,1,door,index,state,time,'')
            # - cancel_alarm:   ControlDevice(handle,2,door,0,0,0,'')
            # - reboot:         ControlDevice(handle,3,0,0,0,0,'')
            # - normal_open:    ControlDevice(handle,4,door,state,0,0,'')
            if action == "control_device":
                ret = int(dll.ControlDevice(int(handle), 1, int(door), int(index), int(state), int(time), reserved))
            elif action == "cancel_alarm":
                ret = int(dll.ControlDevice(int(handle), 2, int(door), 0, 0, 0, reserved))
            elif action == "reboot":
                ret = int(dll.ControlDevice(int(handle), 3, 0, 0, 0, 0, reserved))
            else:  # control_normal_open
                ret = int(dll.ControlDevice(int(handle), 4, int(door), int(state), 0, 0, reserved))

            last_error = _pull_last_error(dll)
            sys.stdout.write(json.dumps({"ok": ret >= 0, "result": ret, "data": "", "last_error": last_error}))
            return 0

        sys.stdout.write(json.dumps(_fail(-3, "unknown action", _pull_last_error(dll))))
        return 0

    except Exception as e:
        sys.stdout.write(json.dumps(_fail(-500, f"exception: {e}", _pull_last_error(dll))))
        return 0

    finally:
        try:
            _disconnect(dll, handle)
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
