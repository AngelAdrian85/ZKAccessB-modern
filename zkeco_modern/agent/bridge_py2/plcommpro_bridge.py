# -*- coding: utf-8 -*-
"""Python 2.6 bridge for ZKTeco plcommpro.dll.

This script is executed by the bundled 32-bit Python shipped with legacy
ZKAccessB (Python 2.6). It performs a single request (connect -> op ->
disconnect) and prints JSON to stdout.

Why this exists:
- plcommpro.dll in this environment is 32-bit (SysWOW64).
- The modern app runs on 64-bit Python 3.x, which cannot load 32-bit DLLs.

Request format (JSON, passed via --request):
{
  "action": "connect"|"get_options"|"set_options"|"query_data"|"data_count"|"search_device"|"modify_ip",
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

import sys
import json
from ctypes import windll, create_string_buffer


def _pull_last_error(dll):
    try:
        return int(dll.PullLastError())
    except Exception:
        return 0


def _load_dll(dll_path):
    if dll_path:
        return windll.LoadLibrary(dll_path)
    # Rely on system search path (legacy behavior).
    return windll.LoadLibrary('plcommpro.dll')


def _connect(dll, comminfo):
    comm_type = int(comminfo.get('comm_type', 1) or 1)
    ip = comminfo.get('ipaddress', '')
    port = int(comminfo.get('ip_port', 4370) or 4370)
    passwd = comminfo.get('password', '')
    timeout = int(comminfo.get('timeout', 3000) or 3000)

    if comm_type == 1:
        params = 'protocol=TCP,ipaddress=%s,port=%d,timeout=%d,passwd=%s' % (ip, port, timeout, passwd)
    else:
        # RS485 not implemented in bridge yet.
        params = 'protocol=RS485,port=%s,baudrate=%sbps,deviceid=%d,timeout=%d,passwd=%s' % (
            comminfo.get('com_port', 'COM1'),
            comminfo.get('baudrate', '9600'),
            int(comminfo.get('com_address', 1) or 1),
            timeout,
            passwd,
        )

    constr = create_string_buffer(params)
    h = int(dll.Connect(constr))
    if h > 0:
        return h

    # Legacy pattern: PullLastError is positive; convert to negative.
    err = _pull_last_error(dll)
    if err > 0:
        err = -err
    return int(err or -1)


def _disconnect(dll, handle):
    try:
        if int(handle) > 0:
            dll.Disconnect(int(handle))
    except Exception:
        pass


def main(argv):
    # optparse for Python 2.6 compatibility
    try:
        from optparse import OptionParser
    except Exception:
        sys.stderr.write('missing optparse\n')
        return 2

    parser = OptionParser()
    parser.add_option('--request', dest='request', default='')
    (opts, _args) = parser.parse_args(argv)

    if not opts.request:
        sys.stdout.write(json.dumps({'ok': False, 'result': -1, 'data': 'missing --request', 'last_error': 0}))
        return 2

    try:
        req = json.loads(opts.request)
    except Exception as e:
        sys.stdout.write(json.dumps({'ok': False, 'result': -1, 'data': 'invalid json: %s' % e, 'last_error': 0}))
        return 2

    action = (req.get('action') or '').strip().lower()
    comminfo = req.get('comminfo') or {}
    dll_path = req.get('dll_path')

    try:
        dll = _load_dll(dll_path)
    except Exception as e:
        sys.stdout.write(json.dumps({'ok': False, 'result': -2, 'data': 'dll load failed: %s' % e, 'last_error': 0}))
        return 2

    handle = 0
    try:
        if action in ('search_device', 'modify_ip'):
            address = str(req.get('address') or '255.255.255.255')
            # UDP operations don't use a connected handle.
            if action == 'search_device':
                dev_buf = create_string_buffer('', 65536)
                ret = int(dll.SearchDevice('UDP', address, dev_buf))
                last_error = _pull_last_error(dll)
                data = ''
                if ret >= 0:
                    data = dev_buf.raw.split('\x00')[0]
                sys.stdout.write(json.dumps({'ok': ret >= 0, 'result': ret, 'data': data, 'last_error': last_error}))
                return 0

            if action == 'modify_ip':
                payload = req.get('payload') or ''
                pbuffer = create_string_buffer(payload)
                ret = int(dll.ModifyIPAddress('UDP', address, pbuffer))
                last_error = _pull_last_error(dll)
                sys.stdout.write(json.dumps({'ok': ret >= 0, 'result': ret, 'data': '', 'last_error': last_error}))
                return 0

        # TCP/RS485 actions: connect first
        handle = _connect(dll, comminfo)
        if int(handle) <= 0:
            last_error = _pull_last_error(dll)
            sys.stdout.write(json.dumps({'ok': False, 'result': int(handle), 'data': 'connect failed', 'last_error': last_error}))
            return 0

        if action == 'connect':
            last_error = _pull_last_error(dll)
            sys.stdout.write(json.dumps({'ok': True, 'result': int(handle), 'data': str(handle), 'last_error': last_error}))
            return 0

        if action == 'get_options':
            items = (req.get('items') or '').strip()
            op_buf = create_string_buffer(2048)
            pitems = create_string_buffer(items)
            ret = int(dll.GetDeviceParam(int(handle), op_buf, 2048, pitems))
            last_error = _pull_last_error(dll)
            data = ''
            if ret >= 0:
                data = op_buf.raw.split('\x00')[0]
            sys.stdout.write(json.dumps({'ok': ret >= 0, 'result': ret, 'data': data, 'last_error': last_error}))
            return 0

        if action == 'set_options':
            items = (req.get('items') or '').strip()
            pitems = create_string_buffer(items)
            ret = int(dll.SetDeviceParam(int(handle), pitems))
            last_error = _pull_last_error(dll)
            sys.stdout.write(json.dumps({'ok': ret >= 0, 'result': ret, 'data': '', 'last_error': last_error}))
            return 0

        if action == 'data_count':
            table = (req.get('table') or '').strip()
            ret = int(dll.GetDeviceDataCount(int(handle), table, '', ''))
            last_error = _pull_last_error(dll)
            sys.stdout.write(json.dumps({'ok': ret >= 0, 'result': ret, 'data': '', 'last_error': last_error}))
            return 0

        if action == 'query_data':
            table = (req.get('table') or '').strip()
            fields = (req.get('fields') or '*').strip()
            flt = (req.get('filter') or '').strip()
            opt = (req.get('option') or '').strip()
            buf_len = int(req.get('buffer_len') or 2097152)
            str_buf = create_string_buffer(buf_len)
            ptable = create_string_buffer(table)
            pfield = create_string_buffer(fields)
            pfilter = create_string_buffer(flt)
            popt = create_string_buffer(opt)
            ret = int(dll.GetDeviceData(int(handle), str_buf, buf_len, ptable, pfield, pfilter, popt))
            last_error = _pull_last_error(dll)
            data = ''
            if ret >= 0:
                data = str_buf.raw.split('\x00')[0]
            sys.stdout.write(json.dumps({'ok': ret >= 0, 'result': ret, 'data': data, 'last_error': last_error}))
            return 0

        sys.stdout.write(json.dumps({'ok': False, 'result': -3, 'data': 'unknown action', 'last_error': _pull_last_error(dll)}))
        return 0

    except Exception as e:
        sys.stdout.write(json.dumps({'ok': False, 'result': -500, 'data': 'exception: %s' % e, 'last_error': _pull_last_error(dll)}))
        return 0

    finally:
        try:
            _disconnect(dll, handle)
        except Exception:
            pass


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
