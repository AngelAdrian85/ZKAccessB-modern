# Progress report (2026-02-17) — ZKAccessB-modern ↔ C3-100Pro (192.168.1.235)

## Goal
Restore a reliable way to actuate relays/doors on ZKTeco C3-100Pro at `192.168.1.235`.

Preferred path was PullSDK (plcommpro.dll + bridge) over TCP (port `14370`), because it is typically safer/easier to harden (server initiates connection). When PullSDK remained blocked after the device reset, the effort pivoted to:
- proving what is and isn’t reachable,
- trying to force `Protype=pull` via UDP config,
- reverse-engineering WebUI CGI endpoints,
- preparing a Push-mode capture path (device → server) because the device persists as `Protype=push`.

## Environment
- OS: Windows
- Python: 3.11 in `.venv`
- Project: Django 4.2 app (`zkeco_modern/`), plus SDK bridges/scripts

## Device facts (high-signal)
From UDP discovery:
- Device: `C3-100Pro`
- IP: `192.168.1.235`
- MAC: `00:17:61:05:3D:CB`
- Firmware/Ver: `AC Ver 4.7.8.3033 Aug 14 2023`
- `Protype=push`
- `IsSupportSSL=1`
- Ports observed:
  - `443` open (TLS works)
  - `14370` open (TCP accepts connect)
  - `4370` refused (closed)

## Summary of what was tried and what we learned

### A) PullSDK connectivity (plcommpro.dll) is still blocked
- Multiple sweeps were done earlier (DLL bundles, ports, password/no password). Current confirmation:
  - Direct ctypes test via `tools/test_plcomm_python_connect.py` using `Resurse/Standalone SDK-6.3.1.55/SDK/x64/plcommpro.dll`:
    - params: `protocol=TCP,ipaddress=192.168.1.235,port=14370,timeout=1000`
    - result: `handle=0`, `sdk_last_error=-2`
    - **elapsed ~23.5 seconds**, despite `timeout=1000`.
- TLS probe on `14370`:
  - `tools/probe_tls_ports.py` shows `443` is TLSv1.2, but `14370` TLS handshake times out.
- Custom plcommpro-binary socket driver probe:
  - `tools/probe_zk_socket_protocol.py` → `connection_timeout` on `14370`, `connection_refused` on `4370`.

**Conclusion:** even though `14370` accepts TCP connections, it does not behave like our expected PullSDK/plcommpro endpoint right now.

### B) UDP `ModifyIPAddress` “succeeds” but `Protype=pull` does not persist
- Existing script `scripts/device_enable_pull_udp.py`:
  - `ModifyIPAddress` returns `{ok: true, result: 0}` but rediscovery still shows `Protype=push`.
- New/expanded experiment `scripts/try_modify_udp_payload.py`:
  - Adds extra fields to payload (clearing WebServer fields) and includes retry-based rediscovery.
  - Result confirmed:
    - Modify returns success.
    - After rediscovery: **still `Protype=push`**.

**Conclusion:** On this firmware/model, `Protype=pull` is not being applied (ignored/overridden). Pull cannot be enabled via this UDP knob alone.

### C) WebUI CGI reverse-engineering: status works, config requires session, login endpoint seems broken
- `https://192.168.1.235/cgi-bin/monitor.cgi`:
  - Works without login.
  - Returns status JSON like:
    - `[{"door1":"0",...,"relay4":"0",...,"alarm4":"0"}]`
- `https://192.168.1.235/cgi-bin/param.cgi`:
  - Returns: `[Failure] Session id error!` and JS redirect.
  - Passing credentials via query string didn’t bypass this.
- `https://192.168.1.235/cgi-bin/login.cgi`:
  - WebUI JS (`device_webui_dump/login.js`) expects:
    - `POST /cgi-bin/login.cgi` with form data:
      - `-username` = Base64(username)
      - `-userpass` = MD5(password)
  - Live probing shows:
    - with `-username` + `-userpass` → `HTTP 500 Internal Server Error`
    - other key names like `-userpwd`, `username/password` → `HTTP 400`

**Conclusion:** we cannot obtain a session via CGI login right now, so we cannot use `param.cgi` and any session-protected remote actions.

### D) “Remote operation” UI mismatch: `openPost()` not present
- `device_webui_dump/remote_operation.html` calls `openPost()` on OK buttons.
- `device_webui_dump/remote_operation.js` is confirmed (re-fetched) to be ~2743 bytes and does **not** define `openPost()`.
- `device_webui_dump/monitor.js` opens `remote_operation.html?operationType=...&relayID=...`.

**Conclusion:** firmware/UI bundle mismatch or missing conditional JS. The real remote-control request path is not visible in the static dump.

## Push-mode pivot (most promising path right now)
Because the device persists as `Protype=push`, we pivoted to capturing push callbacks and then implementing remote actions via the push protocol (once observed).

### What was implemented
1) Minimal HTTP listener to observe incoming push callbacks:
- File: `scripts/push_listener.py`
- Listens on `0.0.0.0:8088`
- Prints full request (method/path/headers/body) and responds `200 OK`.

2) UDP script to set the device’s push server URL/port:
- File: `scripts/set_push_server_udp.py`
- Sets these fields via UDP ModifyIPAddress:
  - `WebServerURL=http://192.168.1.2:8088`
  - `WebServerIP=192.168.1.2`
  - `WebServerPort=8088`
  - Keeps `Protype=push`

### What was verified
- After running `scripts/set_push_server_udp.py`, UDP rediscovery shows:
  - `WebServerURL=http://192.168.1.2:8088`
  - `WebServerIP=192.168.1.2`
  - `WebServerPort=8088`
  - `Protype=push` unchanged

### Current blocker
- Windows Firewall inbound rule for port `8088` could not be added without elevation.
  - Attempted `netsh advfirewall ...` failed: “requires elevation (Run as administrator)”.
- Listener was verified locally (curl to `127.0.0.1:8088/test` works), but no device callbacks were seen yet.

## Files created/modified in this effort
- Created: `scripts/push_listener.py`
- Created: `scripts/set_push_server_udp.py`
- Modified: `scripts/try_modify_udp_payload.py` (added rediscovery retries, MAC lookup, directed broadcast)

## Next steps (actionable)
1) Allow inbound TCP/8088 only from the device IP (run as Administrator):
   - `netsh advfirewall firewall add rule name="ZKPush 8088" dir=in action=allow protocol=TCP localport=8088 remoteip=192.168.1.235`
   - (Or add the rule via Windows Defender Firewall UI.)

2) Reboot/power-cycle the controller.
   - Many panels only re-read push/ADMS settings after reboot.

3) Keep `scripts/push_listener.py` running and capture the first callback.
   - Once we see the exact path/query/body the panel sends, we can:
     - implement a proper push endpoint inside the Django app, and
     - reply/emit the correct command format to trigger remote door/relay operations.

4) If push never arrives:
   - Verify L2 reachability from device to server (`192.168.1.2:8088`) and router ACLs.
   - Confirm whether the device expects HTTP vs HTTPS for WebServerURL.

## Notes / security guidance (LAN)
- Prefer pull-mode when possible (server initiates), but for this device/firmware we currently can’t enable it.
- For push-mode, keep it LAN-only and firewall the listener strictly to the device IP.
- Do not expose device WebUI/ports to the internet.
