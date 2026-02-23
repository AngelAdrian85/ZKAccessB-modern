from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def _pe_machine(path: Path) -> int | None:
    try:
        b = path.read_bytes()
        if len(b) < 0x40 or b[:2] != b"MZ":
            return None
        pe_off = int.from_bytes(b[0x3C:0x40], "little")
        if pe_off <= 0 or pe_off + 6 >= len(b):
            return None
        if b[pe_off : pe_off + 4] != b"PE\x00\x00":
            return None
        return int.from_bytes(b[pe_off + 4 : pe_off + 6], "little")
    except Exception:
        return None


def _arch_name(machine: int | None) -> str:
    if machine is None:
        return "unknown"
    if machine == 0x014C:
        return "x86"
    if machine == 0x8664:
        return "x64"
    return f"0x{machine:04X}"


def _filter_bad_syspath() -> None:
    bad_path_markers = ("ZKTeco", "python-support", "Python26")
    sys.path[:] = [p for p in sys.path if not (p and any(m in p for m in bad_path_markers))]


def main() -> int:
    _filter_bad_syspath()
    repo_root = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, os.path.join(repo_root, "zkeco_modern"))

    from agent.plcommpro_bridge import PlcommproConnInfo, connect_only, default_plcommpro_dll_path

    ip = os.environ.get("ZK_IP", "192.168.1.235").strip()
    port = int(os.environ.get("ZK_PORT", "14370").strip())
    pw = os.environ.get("ZK_COMM_PASSWORD", "").strip()

    dll_default = default_plcommpro_dll_path()
    print("default dll:", dll_default)

    bridge_x86 = os.path.join(
        repo_root,
        "zkeco_modern",
        "agent",
        "bridge_dotnet",
        "PlcommproBridgeRunner",
        "bin",
        "Release",
        "net8.0",
        "win-x86",
        "publish",
        "PlcommproBridgeRunner.exe",
    )
    bridge_x64 = os.path.join(
        repo_root,
        "zkeco_modern",
        "agent",
        "bridge_dotnet",
        "PlcommproBridgeRunner",
        "bin",
        "Release",
        "net8.0",
        "win-x64",
        "publish",
        "PlcommproBridgeRunner.exe",
    )
    print("bridge x86:", bridge_x86 if os.path.exists(bridge_x86) else "(missing)")
    print("bridge x64:", bridge_x64 if os.path.exists(bridge_x64) else "(missing)")

    candidates = [
        dll_default,
        os.path.join(repo_root, "Resurse", "ZKEUBioAccessSetup", "Dependencies", "ZKAccess3.5", "NewSDK", "plcommpro.dll"),
        os.path.join(repo_root, "Resurse", "Standalone SDK-6.3.1.55", "PullSDK", "plcommpro.dll"),
        os.path.join(repo_root, "Resurse", "Standalone SDK-6.3.1.55", "SDK", "x64", "plcommpro.dll"),
    ]

    seen: set[str] = set()
    for d in candidates:
        if not d or d in seen:
            continue
        seen.add(d)
        print("\n== try dll ==", d)

        # Pick an appropriate bridge runner based on DLL architecture.
        try:
            mach = _pe_machine(Path(d))
            arch = _arch_name(mach)
        except Exception:
            arch = "unknown"
        if arch == "x64" and os.path.exists(bridge_x64):
            os.environ["ZKACCESS_BRIDGE_EXE"] = bridge_x64
        elif os.path.exists(bridge_x86):
            os.environ["ZKACCESS_BRIDGE_EXE"] = bridge_x86
        print("dll arch:", arch)
        print("bridge set:", os.environ.get("ZKACCESS_BRIDGE_EXE", ""))

        conn = PlcommproConnInfo(ipaddress=ip, ip_port=port, password=pw, timeout=30000, protocol="TCP")
        t0 = time.time()
        try:
            r = connect_only(conn, dll_path=d, process_timeout_s=40)
        except Exception as e:
            r = {"ok": False, "exc": str(e)}
        dt = time.time() - t0
        print("elapsed_s=", round(dt, 2))
        print(json.dumps(r, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
