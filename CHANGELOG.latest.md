# Changelog — latest save

Commit: fbeddc0a — "Major update: ZKTech integration + bridge + provisioning + docs"
Merged into: main
Date: 2026-02-23
Author: local workspace

Summary
-------
Major project sync bringing in the latest device integration work (ZKTeco/ZKTech), bridge runners, provisioning flows, new migrations, tooling, and documentation.

High-level changes
------------------
- Added ZKTech/ZKTeco integration docs (guides, quick start, test results) and project progress reports.
- Added bridge implementations (Python / Python2 compatibility + .NET runner sources) and drivers for device communication.
- Added/updated device provisioning, CommCenter/tray agent flows, and WebSocket/UI plumbing.
- Added new migrations and tests supporting the updated model + provisioning behavior.

Notes
-----
- Build outputs (e.g. `.NET bin/obj`) and large local resources/dumps are intentionally excluded from Git.

---

Commit: 0aef9f36 — "UI: unified Action Modal feedback + dashboard backup modal"
Merged into: main
Date: 2026-01-16
Author: local workspace

Summary
-------
Rapid UI/UX upgrade focused on consistent, lightweight operation feedback across modules (IMPORT / EXPORT / UPDATE / ȘTERGERE): one unified Action Modal with Romanian live messages, operation-only animations, and better success/error visuals. Also reused the existing “Se încarcă pagina…” spinner as a global Busy Overlay and wired Dashboard backup to show proper progress/success/failure feedback.

High-level changes
------------------
- Consistent operation animation during `loading` (spinner + progress) inside Action Modal; no heavy blur/glow/open-close animations.
- Reused the same spinner from the navigation loading overlay for a consistent look across the app.
- Added nicer success/error backgrounds (green/red) for final states: EXPORT/IMPORT/UPDATE/ȘTERGERE.
- Added a global Busy Overlay API (`window.zkBusy`) that can be used anywhere for quick feedback.
- Dashboard: backup now shows modal progress + success/error; Server/DB badges now reflect live status instead of staying static.

Files changed (main)
-------------------
- M zkeco_modern/agent/templates/agent/base_legacy.html — Busy Overlay + Action Modal spinner unification + success/error styling.
- A zkeco_modern/agent/templates/agent/base_embed_legacy.html — same UI parity for embedded tabs.
- M zkeco_modern/agent/templates/agent/menu_access.html — UPDATE/ȘTERGERE operations wrapped with Action Modal feedback.
- M zkeco_modern/agent/templates/agent/segments_crud_list.html — UPDATE/ȘTERGERE operations wrapped with Action Modal feedback.
- M zkeco_modern/agent/templates/agent/menu_personnel.html — logs export uses Action Modal feedback.
- M zkeco_modern/agent/templates/agent/menu_personnel_modern.html — logs export uses Action Modal feedback.
- M zkeco_modern/agent/templates/agent/access_dashboard.html — backup uses modal feedback; live Server/DB badge updates.

---

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
