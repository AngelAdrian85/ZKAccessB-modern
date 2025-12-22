# Changelog — latest save

Commit: 69fb99e6 — "Fix: DeviceStatus updated_at handling and UI timestamp consistency"
Merged into: main (merge commit 5d9660eb)
Date: 2025-12-22
Author: (merged branch commits)

Summary
-------
Small-to-medium refactor and bug-fix focused on ensuring the UI and DB show authoritative device `updated_at` timestamps, avoiding false timestamps created at process startup, and aligning dashboard/device-list timestamp presentation. Also added runtime/test scripts and some housekeeping files.

High-level changes
------------------
- Prevent CommCenter/tray startup from writing the server start time into `DeviceStatus.updated_at`.
- Persist `updated_at` only when a genuine device state transition occurs (e.g., offline->online with evidence such as rtlog) or when UI actions cause a true change.
- Ensure `readers_start`, `readers_stop` and `trigger_readers_start` update `DeviceStatus.updated_at` only when `online` actually changes; they do not create `DeviceStatus` rows on startup.
- Annotate device queryset used in the devices list with the latest `DeviceStatus` values and expose ISO timestamps to client-side JS for consistent browser-local rendering.
- Add runtime broadcast file to help correlate WS messages with DB state and added a collection of simulation and diagnostic scripts for testing.
- Minor tray-agent housekeeping and archival of previous `tray_agent.py` as `tray_agent.VECHE.py`.

Files changed (representative groups)
------------------------------------
Note: `M` = modified, `A` = added, `R` = renamed.

Core backend
- M zkeco_modern/agent/modern_comm_center.py — Adjusted `connect_all` to avoid creating DeviceStatus on startup; persist `updated_at` only on real transitions and broadcast appropriate timestamps.
- M zkeco_modern/agent/views.py — `readers_start`, `readers_stop`, `access_dashboard`, `devices_crud_list` updated: only update `DeviceStatus` when state changes; dashboard uses DB `updated_at`; device list annotated with Subquery latest `updated_at`.
- M zkeco_modern/agent/management/commands/trigger_readers_start.py — Only updates `updated_at` for devices whose `online` changes; broadcasts per-device.
- M zkeco_modern/agent/management/commands/tray_agent.py — housekeeping changes for tray interactions (best-effort updates; renamed backup of old file present).
- M zkeco_modern/agent/consumers.py — small adjustments related to WS consumers (message payloads include `updated_at`).
- A zkeco_modern/agent/management/commands/dump_device_statuses.py — new helper command to dump DeviceStatus rows for diagnostics.

Templates & UI
- M zkeco_modern/agent/templates/agent/devices_crud_list.html — updated to include ISO `data-ts` attributes and client-side formatting to browser local time.
- M zkeco_modern/agent/templates/agent/access_dashboard.html — ensure initial page render uses DB `updated_at` values.

Models / WS
- A zkeco_modern/agent/ws.py — helper to broadcast device status (include `updated_at`).

Runtime / scripts / tests
- A runtime_logs/last_status_broadcasts.json — runtime artifact with last broadcast timestamps per device.
- A runtime_logs/device_status_backup_*.json and runtime_scripts/* — added a suite of simulation and test scripts to reproduce startup/start/stop scenarios and collect DB/WS traces.

Misc
- M tray_launch.ps1, auto_run.ps1 — local scripts updated.
- R zkeco_modern/tray_agent.py -> zkeco_modern/tray_agent.VECHE.py — previous tray agent archived.
- A zkeco_modern/backups/db_backup_manual_20251222_082729.sql (and other manual backups) — added backups (large SQL files).
- M zkeco_modern/agent_controller.ini — small config edits.

Notes & rationale
-----------------
- `DeviceStatus.updated_at` is defined as `auto_now=True` in the model. That means any save that includes updating fields may change the timestamp. The changes aim to avoid unintended saves at CommCenter/tray startup that would stamp the DB with the server start time. Instead, the code now:
  - Skips creating status rows at CommCenter startup.
  - Only sets `online=True` and `updated_at` when there is evidence of device responsiveness (rtlog) or when the saved row previously recorded `online=False` and is transitioning to `True`.
  - `readers_stop` records `updated_at` when moving devices `offline`.
- For UI consistency, the device list now pulls the authoritative DB timestamp and renders it client-side to eliminate timezone/offset mismatches.
- New runtime scripts are intended for local simulation and debugging only; they do not run automatically in production.

Safe deployment guidance
------------------------
- Restart the CommCenter/tray services after deploying these changes so the runtime behavior aligns with the new logic.
- If you prefer devices created via the UI to immediately have a `DeviceStatus` row, decide on a creation policy (e.g., create with `online=False` and no `updated_at` or set `updated_at` equal to device `created_at`). Current code intentionally avoids creating `DeviceStatus` on device add to prevent server-start timestamps.
- Review large backup files added under `zkeco_modern/backups/` — keep only what you need in the repo, or consider removing/binarizing them (they bloat the Git repo).

How to apply or revert
----------------------
- This changelog is non-destructive. If you want me to commit this changelog into the repo or create a `CHANGELOG.md` and commit it to `main`, confirm and I will create the file and optionally commit/push.
- If you want a more granular per-file explanation (short paragraph per changed file), I can generate that next.

---

Generated by the local workspace analysis (no commits made by this operation). If you want this changelog added to the repository as `CHANGELOG.md` and committed to `main`, reply `commit changelog` and I will create and commit it.
