"""Quick inventory/check for repo-shipped SDK resources (Resurse) and bridge runner.

Goal: confirm that this workspace contains the minimum components required to talk to
ZKTeco controllers via plcommpro.dll using the x86 .NET bridge.

This does NOT connect to a controller. It only checks file presence/architecture and
optionally does a local DLL load smoke via SearchDevice.

Usage:
    .venv/Scripts/python.exe tools/check_resurse_components.py
    .venv/Scripts/python.exe tools/check_resurse_components.py --dll "Resurse/Standalone SDK-6.3.1.55/PullSDK/plcommpro.dll" --load-test
"""

from __future__ import annotations

import argparse
import json
import os
import struct
import subprocess
import sys
from pathlib import Path
from typing import Optional


def _pe_machine(path: Path) -> Optional[int]:
    try:
        if not path.exists() or not path.is_file():
            return None
        b = path.read_bytes()
        if len(b) < 0x40 or b[:2] != b"MZ":
            return None
        pe_off = struct.unpack_from("<I", b, 0x3C)[0]
        if pe_off <= 0 or pe_off + 6 >= len(b):
            return None
        if b[pe_off : pe_off + 4] != b"PE\x00\x00":
            return None
        return struct.unpack_from("<H", b, pe_off + 4)[0]
    except Exception:
        return None


def _arch_name(machine: Optional[int]) -> str:
    if machine is None:
        return "unknown"
    if machine == 0x014C:
        return "x86"
    if machine == 0x8664:
        return "x64"
    return f"0x{machine:04X}"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_bridge_exe() -> Optional[Path]:
    root = _repo_root()
    cand = (
        root
        / "zkeco_modern"
        / "agent"
        / "bridge_dotnet"
        / "PlcommproBridgeRunner"
        / "bin"
        / "Release"
        / "net8.0"
        / "win-x86"
        / "publish"
        / "PlcommproBridgeRunner.exe"
    )
    return cand if cand.exists() else None


def _default_bridge_exe_x64() -> Optional[Path]:
    root = _repo_root()
    cand = (
        root
        / "zkeco_modern"
        / "agent"
        / "bridge_dotnet"
        / "PlcommproBridgeRunner"
        / "bin"
        / "Release"
        / "net8.0"
        / "win-x64"
        / "publish"
        / "PlcommproBridgeRunner.exe"
    )
    return cand if cand.exists() else None


def _plcommpro_candidates() -> list[Path]:
    root = _repo_root()
    return [
        root / "Resurse" / "Standalone SDK-6.3.1.55" / "PullSDK" / "plcommpro.dll",
        root / "Resurse" / "ZKEUBioAccessSetup" / "Dependencies" / "PullSDK" / "plcommpro.dll",
        root / "Resurse" / "ZKEUBioAccessSetup" / "Dependencies" / "ZKAccess3.5" / "NewSDK" / "plcommpro.dll",
        root / "Resurse" / "ZKEUBioAccessSetup" / "Dependencies" / "ZKAccess3.5" / "pullsdk" / "plcommpro.dll",
        root / "Resurse" / "SDK-Ver2.2.0.220" / "plcommpro.dll",
        root / "Resurse" / "Standalone SDK-6.3.1.55" / "SDK" / "x86" / "plcommpro.dll",
        root / "Resurse" / "Standalone SDK-6.3.1.55" / "SDK" / "x64" / "plcommpro.dll",
    ]


def _check_deps(dll_path: Path) -> list[str]:
    # Not all bundles ship all of these, but missing core ones is a red flag.
    deps = [
        "plcomms.dll",
        "pltcpcomm.dll",
        "plrscomm.dll",
        "plrscagent.dll",
    ]
    missing: list[str] = []
    d = dll_path.parent
    for name in deps:
        if not (d / name).exists():
            missing.append(name)
    return missing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dll", default="", help="Path to plcommpro.dll to check")
    ap.add_argument(
        "--load-test",
        action="store_true",
        help="Run a minimal bridge call to ensure plcommpro.dll can be loaded",
    )
    args = ap.parse_args()

    root = _repo_root()

    print(f"Repo root: {root}")

    bridge = _default_bridge_exe()
    bridge64 = _default_bridge_exe_x64()
    if bridge:
        print(f"Bridge EXE (x86): OK ({bridge})")
        print(f"  arch={_arch_name(_pe_machine(bridge))}")
    else:
        print("Bridge EXE (x86): MISSING (expected publish output)")

    if bridge64:
        print(f"Bridge EXE (x64): OK ({bridge64})")
        print(f"  arch={_arch_name(_pe_machine(bridge64))}")
    else:
        print("Bridge EXE (x64): MISSING (optional)")

    dlls = _plcommpro_candidates()
    chosen = Path(args.dll).resolve() if args.dll else None

    print("\nplcommpro.dll candidates:")
    for p in dlls:
        exists = p.exists()
        arch = _arch_name(_pe_machine(p)) if exists else "n/a"
        tag = "*" if chosen and p.samefile(chosen) else " "
        print(f"{tag} {p} :: {'OK' if exists else 'MISSING'} :: {arch}")

    if chosen:
        if not chosen.exists():
            print(f"\n[FAIL] --dll not found: {chosen}")
            return 2
        print(f"\nSelected DLL: {chosen} (arch={_arch_name(_pe_machine(chosen))})")
        missing = _check_deps(chosen)
        if missing:
            print(f"[WARN] Missing sibling dependencies in {chosen.parent}: {missing}")
        else:
            print("Dependencies: OK (common siblings present)")

        if args.load_test:
            dll_arch = _arch_name(_pe_machine(chosen))
            bridge_for_test = bridge64 if dll_arch == "x64" else bridge
            if not bridge_for_test:
                print(f"[FAIL] Cannot load-test {dll_arch} DLL without matching bridge EXE")
                return 3

            req = {
                "action": "load_only",
                "dll_path": str(chosen),
            }
            env = {**os.environ}
            env["PYTHONNOUSERSITE"] = "1"
            env["PYTHONPATH"] = ""
            env["PATH"] = str(chosen.parent) + os.pathsep + (env.get("PATH") or "")

            print("\nLoad-test: running bridge load_only ...")
            cp = subprocess.run(
                [str(bridge_for_test), "--request", json.dumps(req)],
                capture_output=True,
                text=True,
                timeout=8,
                env=env,
            )
            out = (cp.stdout or "").strip()
            if not out:
                print(f"[FAIL] Bridge returned no output. stderr={cp.stderr!r}")
                return 4
            try:
                resp = json.loads(out)
            except Exception as ex:
                print(f"[FAIL] Bridge output not JSON: {ex}")
                print(out[:2000])
                return 5
            ok = bool(resp.get("ok"))
            print(f"Load-test result: ok={ok} result={resp.get('result')} last_error={resp.get('last_error')}")
            # We don't require a successful discovery; we only care that the call executes.

    else:
        print("\nTip: pass --dll <path> to validate dependencies + optional --load-test")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
