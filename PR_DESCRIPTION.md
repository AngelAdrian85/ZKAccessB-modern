# PR: controller route diagnostics, W26 correlation, monitor hardening, and backup sync

Summary
-------
This changeset brings the repository to the current working state used to diagnose controller 22, correlate missing-card controller events with raw Wiegand captures, harden the monitor/tray diagnostics, and preserve the project in cloud Git so the same state can be resumed on another machine.

What I changed
--------------
- Added controller capability, provisioning, decoder, port-diagnostic, and pyzk probe helpers for the C3-100Pro / ZMM200_C3Pro route investigation.
- Added the Wiegand decoder and raw capture pipeline pieces used to recover unknown-card numbers when firmware omits `CardNo`.
- Added `DeviceRealtimeLog.correlation_payload` plus supporting migration and CommCenter correlation logic.
- Added Wiegand format CRUD support and the embedded Wiegand UI.
- Added controller 22 capture tools: W26 listener startup, zkemkeeper bridge helpers, long-capture scripts, decode helpers, and runbooks.
- Hardened `monitor.html`, `monitor_embed.html`, `views.py`, and `tray_agent.py` so UI/tray explicitly report `raw capture absent` and `zkemkeeper error` instead of implying decode readiness from stale state.
- Added tests covering route resolution, decoders, Wiegand decode/push behavior, capture arm helpers, CommCenter exclusive-capture guard, and related monitor/probe flows.
- Added a dated backup note and refreshed changelog material for the current cloud save.

Why
---
The project needed a cloud-synced checkpoint that preserves the latest controller 22 investigation state, including the software path now proven to accept raw W26 frames and the operational documentation required to continue live swipe testing from another workstation.

Files to review
---------------
- `tray_launch.ps1`
- `zkeco_modern/agent/views.py`
- `zkeco_modern/agent/modern_comm_center.py`
- `zkeco_modern/agent/management/commands/tray_agent.py`
- `zkeco_modern/agent/uid_correlation.py`
- `zkeco_modern/agent/wiegand_decoder.py`
- `zkeco_modern/agent/controller_capabilities.py`
- `zkeco_modern/agent/controller_provisioning.py`
- `scripts/wiegand_listener.py`
- `scripts/start_w26_tap_capture.ps1`
- `scripts/send_w26_test_frame.ps1`
- `HARDWARE_W26_TAP_GUIDE.md`

Notes
-----
- Local runtime artifacts and cookies are intentionally excluded from Git.
- `zkemkeeper` remains in error for controller 22, but the W26 software path has been validated independently through injected test frames.
- After pulling this state elsewhere, the next operational step is a real physical swipe on the reader whose W26 lines are actually tapped.
