# plcommpro Bridge (no 32-bit Python)

This folder contains a small **x86** .NET console app that calls `plcommpro.dll` and speaks JSON over stdout.

Why:
- Many ZKTeco installs ship **32-bit** `plcommpro.dll`.
- 64-bit Python cannot load 32-bit DLLs.
- This bridge runs as an **x86 process** on 64-bit Windows (no Python 32-bit needed).

## Build

From repo root:

```powershell
cd zkeco_modern/agent/bridge_dotnet/PlcommproBridgeRunner

dotnet publish -c Release -r win-x86 /p:PublishSingleFile=true /p:SelfContained=true
```

Output exe:
- `bin/Release/net8.0/win-x86/publish/PlcommproBridgeRunner.exe`

## Configure

Set one of these env vars to point at the exe:
- `ZKACCESS_BRIDGE_EXE` (preferred)

Optional:
- `ZKACCESS_PLCOMMPRO_DLL` to point at `plcommpro.dll` if it’s not in `C:\Windows\SysWOW64`.
