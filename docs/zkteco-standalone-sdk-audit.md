# ZKTeco Standalone SDK Audit

Source reviewed:
- `Resurse/ZKTeco_Standalone_SDK_Development_Manual_V2.2_A.3-EN.pdf`
- extracted text snapshot: `tmp_sdk_manual_extract.txt`
- SDK demos under `Resurse/Standalone SDK-6.3.1.55/Demo/`

This audit is the manual-to-application map for the current Django codebase. It focuses on where the manual matches the app, where the app intentionally diverges, and where our previous assumptions were too broad.

## Executive Findings

1. The biggest modeling mistake was treating ZKEMKeeper real-time events as a generally reliable card-capture path for C3 access panels.
   The manual marks `RegEvent`, `ReadRTLog`, `GetRTLog`, `OnHIDNum`, `OnVerify`, `OnAttTransactionEx`, and related callbacks as applicable to `B&W`, `TFT`, and `IFACE` devices. It does not explicitly grant that same guarantee to `C3/F3/G` access panels.

2. For this repository's actual target hardware, `C3-100Pro / ZMM200_C3Pro`, the authoritative transports remain:
   - `plcommpro` bridge for mixed-generation parity and controller table CRUD
   - direct socket driver for C3/F3/G real-time logs and relay control
   - hardware Wiegand tap as the robust fallback when controller-side software paths do not expose the unknown card number

3. The manual's real-time flow was implemented correctly in bridge code, but that does not prove the firmware family will emit those events on this controller.
   Current code already follows the documented sequence:
   - `SetCommPasswordEx` or `SetCommPassword`
   - `Connect_Net`
   - `RegEvent(..., 65535)`
   - active `ReadRTLog`/`GetRTLog` pumping
   - `OnHIDNum` plus `GetHIDEventCardNumAsStr`

4. The app runtime had a separate operational bug: tray status and cleanup logic still assumed only the PowerShell bridge existed, while runtime now prefers the VBS engine. That mismatch is fixed by this change.

## Manual Sections That Matter Most To This App

### PULL SDK Facts For C3

For C3 access controllers, the most useful SDK surface is the PULL SDK family around controller transport and controller tables:

- `Connect`
- `GetDeviceData`
- `GetRTLog`
- `GetDeviceParam`
- `SetDeviceParam`

In this repo those capabilities already exist through the `plcommpro` bridge and direct socket driver layers. The key operational rule is:

- `GetDeviceData(...)` is necessary for controller tables and transaction queues
- `GetRTLog` is necessary for the best available real-time path
- table reads alone are not sufficient for unknown-card capture

That matches field evidence from controller 22, where pure table paths did not expose the live unknown-card number while RT/log-driven flows remained the only software path with a chance to do so.

### 2.2 Common Processes

The diagrams matter more than the individual COM signatures because they define the expected sequencing.

- `2.2.4 Downloading User Information, or Fingerprint Templates`
  The manual shows `ReadAllUserID` / `SSR_GetUserInfo` followed by card retrieval via `CardNumber` attribute or `GetStrCardNumber`, then template retrieval. In this app, the analogous controller-side user/card lookup is done through controller tables, not through SDK user-attribute iteration, because C3 panels are handled better via `plcommpro` and socket transports.

- `2.2.5 Receiving Real-time Events`
  The manual shows two modes:
  - active pull: `ReadRTLog` then `GetRTLog`
  - registered events: `RegEvent`
  Our ZKEMKeeper bridges implement both ideas together because many devices only trigger callbacks while the real-time queue is actively pumped.

- `2.2.6 Enrolling Users Online`
  The manual centers on terminal-style enrollment flows such as `SSR_SetUserInfo`, `SetStrCardNumber`, and `SSR_SetUserTmpStr`. The app does not implement this exact COM enrollment workflow because personnel sync for C3 is modeled through controller tables (`user`, `userauthorize`, `timezone`) rather than biometric-terminal SDK upload flows.

### 3 Related Attributes

- `3.8 GetStrCardNumber`
  This is a user-information attribute query, not a generic unknown-card scan API. It only helps after a user context has already been obtained. That means it is not the right primitive for an unregistered card swiped on controller 22.

- `3.9 SetStrCardNumber`
  Relevant for biometric-terminal enrollment, not for the current C3 personnel sync path.

- `3.10 IsNewFirmwareMachine`
  Useful to distinguish firmware families in pure SDK integrations. In this repository, family handling is done from controller identity, firmware strings, and transport capability mapping rather than through this COM helper.

- `3.11 GetDeviceFirmwareVersion`
  Semantically valid, but not our primary source. We obtain stronger evidence from firmware web endpoints and controller options.

### 4 Real-time Event Functions

- `4.1.1 RegEvent`
  Implemented in both bridge engines. Event mask `65535` matches the manual's all-events guidance.

- `4.1.2 ReadRTLog`
  Implemented in the VBS bridge as part of active pumping.

- `4.1.3 GetRTLog`
  Implemented in both ZKEMKeeper bridge logic and the `plcommpro`/socket driver stack, but these are not equivalent APIs across device families.

- `4.2.5 OnAttTransaction`
  Manual says `Applicable to B&W` only. This is a direct warning against treating it as a universal event contract.

- `4.2.6 OnAttTransactionEx`
  Manual broadens this to `B&W, TFT, IFACE`. The app already captures and forwards it, but the live C3 route did not emit it.

- `4.2.12 OnHIDNum`
  This remains the best documented software event for raw card capture on supported SDK devices. The app extracts from it correctly. The mistake was assuming that C3 access panels will necessarily publish it in practice.

- `4.2.15 OnVerify`
  Correctly forwarded when present, but it is an observed-event path, not a guarantee.

### 5.1 Device Connection Functions

- `5.1.1 Connect_Net`
  Manual notes default port `4370`. This is a default, not a contract. Our live C3 controller reports `TCPPort=14370`, so route-aware port resolution in the app is correct and should not be simplified back to `4370`.

- `5.1.2 Connect_Com` and `5.1.3 Connect_USB`
  Not relevant to the current Windows network deployment for C3 controller 22.

- `5.1.4 Disconnect`
  Implemented conceptually in both bridge/session layers.

## Function Family Audit Against The App

The manual covers a very broad SDK surface. The app should not implement all of it because much of it targets biometric terminals rather than access panels.

### Implemented Or Intentionally Modeled

- Connection and route handling
  - `Connect_Net` semantics are present in the ZKEMKeeper bridge and in route-aware controller probing.
  - C3 route and firmware capability evidence is modeled in `zkeco_modern/agent/controller_capabilities.py`.

- Real-time event ingestion
  - `RegEvent`, `ReadRTLog`, `GetRTLog`, `OnHIDNum`, `OnAttTransactionEx`, `OnVerify`
  - Implemented by `scripts/zkemkeeper_event_bridge.vbs` and `scripts/zkemkeeper_event_bridge.ps1`
  - Normalized into the app by `zkeco_modern/agent/views.py`

- Controller live logs and transaction reads for C3/F3/G
  - Implemented by `zkeco_modern/agent/drivers/plcommpro_bridge_driver.py`
  - Implemented by `zkeco_modern/agent/drivers/zk_socket_driver.py`
  - This is the correct primary path for access panels in this repo

- User/card download for access panels
  - Instead of `ReadAllUserID` + `SSR_GetUserInfo` + `GetStrCardNumber`, the app queries the controller `user` table and builds PIN-to-card maps.

- Access control configuration
  - Manual concepts like time zones, groups, and access control are represented through Django models and synchronized to controller tables.

### Partially Implemented Or Deliberately Deferred

- Attendance-history SDK families (`ReadGeneralLogData`, `SSR_GetGeneralLogData`, etc.)
  The repo focuses on access panels, controller transactions, and monitor flows, not the full attendance-terminal log API surface.

- Biometric template upload/download families
  Fingerprint and face template lifecycle is not implemented as a first-class end-to-end feature in the modern app.

- SMS, holiday, DST, bell schedule, user photo, personalize/app-role functions
  These exist in the manual but are outside the effective scope of the current access-control modernization.

### Not A Good Fit For C3 Access Panels

- `GetStrCardNumber` and `SetStrCardNumber`
  Useful for biometric-terminal user attribute flows, not for unknown-card extraction on live C3 controller traffic.

- Real-time callback assumptions from section 4
  The bridge code is correct, but treating those events as mandatory behavior on C3 was the wrong assumption.

## Where The App Was Wrong

### 1. We over-generalized the ZKEMKeeper event model

The manual explicitly scopes section 4 real-time event APIs to `B&W`, `TFT`, and `IFACE`. Our earlier reasoning treated `OnHIDNum` as if it were a controller-family-neutral truth source for C3. That is not supported by the manual.

### 2. We mixed two product families under one mental model

This repository targets legacy ZKTeco access panels and modernized access workflows. The manual covers standalone fingerprint, attendance, face, and card devices under one COM SDK. Not every documented API belongs to the C3 controller family.

### 3. We treated `GetStrCardNumber` as more useful than it is for unknown cards

The manual describes it as a way to query the card number attribute after user information is already available. That means it cannot solve the `unknown card not enrolled in controller` problem by itself.

### 4. We had a runtime mismatch around the preferred bridge engine

The tray/runtime code still checked only for `zkemkeeper_event_bridge.ps1` in some places, even though runtime now prefers `zkemkeeper_event_bridge.vbs`. That created false status/cleanup behavior.

## Current Recommended Transport Strategy

For this repo and this hardware family:

1. Use `plcommpro` or socket-native flows for C3/F3/G controller CRUD, logs, and door operations.
2. Treat ZKEMKeeper callbacks as opportunistic evidence only, not guaranteed controller behavior.
3. For unknown-card extraction when controller software paths still hide the raw card number, use passive Wiegand capture and push into `card_read_push`.

## Files That Encode The Correct Direction

- `zkeco_modern/agent/drivers/zk_socket_driver.py`
  C3/F3/G direct socket driver

- `zkeco_modern/agent/drivers/plcommpro_bridge_driver.py`
  authoritative mixed-generation bridge logic with transaction and rtlog fallback

- `zkeco_modern/agent/views.py`
  normalizes Wiegand and ZKEMKeeper payloads into monitor/app state

- `scripts/zkemkeeper_event_bridge.vbs`
  current best-effort COM event bridge for supported SDK event families

- `scripts/wiegand_listener.py`
  robust hardware fallback ingestion path

## Practical Conclusion

The right conclusion from the manual is not "implement every COM function everywhere". The right conclusion is:

- implement the SDK functions that match the actual controller family and product scope
- do not treat biometric-terminal COM event contracts as guaranteed behavior on C3 access panels
- keep the app's mainline on `plcommpro` and C3 socket transports
- use Wiegand hardware capture when the controller does not expose unknown-card numbers through software events