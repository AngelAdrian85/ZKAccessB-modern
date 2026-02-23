# Progress report (part 2) — 2026-02-17

## Context
- Device: ZKTeco C3-100Pro @ `192.168.1.235`
- Observed: UDP discovery works; device persists in `Protype=push`; PullSDK connection still blocked even after manual-derived default comm password (`Zk@123`) was tried across multiple `plcommpro.dll` bundles.

## What changed in repo (since part 1)
- Improved the existing push capture script (no new servers added to the Django app):
  - `scripts/push_listener.py` now logs remote IP, parses query params, dumps requests to disk (`push_dumps/`), and provides a simple `/iclock/getrequest` file-backed reply (`adms_commands.txt`) to help observe ADMS/push behavior.
  - `scripts/set_push_server_udp.py` now infers `WebServerIP` + `WebServerPort` from `--server-url` so panels that rely on explicit IP/port fields also work.

## Manual findings
- From `Resurse/ZK_C3-X00 Plus Series_User Manual_20250814.pdf`:
  - Default communication password (for first change) shown as `Zk@123`.
  - Notes indicate device can be factory reset to revert communication password to default.

## Current status
- PullSDK still fails to connect on TCP 14370 with errors `-2` / `-10054` depending on DLL bundle, even when using `Zk@123`.
- Push approach is prepared for capture, but the work is paused now because focus shifts back to the UI/DB flow for creating a new controller in the app.

## Next focus (user request)
Implement the exact UI flow for creating a new controller from scan results:
1) Search controllers button → opens scan modal.
2) Scan is started manually from within the modal.
3) Results list: show **Add** only for items not in DB; show **Edit** for items already present; do not leave the current form.
4) Add modal shows identification fields + checkbox **Stergere datelor de pe centrala**.
   - If checked, after Save show an active progress/status message while running the already-existing wipe function.
   - On success, user must click Continue to proceed.
5) Open a **new controller configuration** modal (separate from existing static edit), with door count determined during scanning/driver detection.
6) Door editing returns to the configuration modal; the config modal stays open.
7) Only after doors are configured, user clicks **Salveaza noua centrala**.
   - Run a validation script; if any condition fails → create nothing.
   - If OK → create device, show centered success status message.
8) Created controller must appear online everywhere in the app.
