"""Minimal Python wrapper around plcommpro.dll.

This exists to support quick local tests like:

    from plcomm import *
    h = Connect("protocol=TCP,...")

Note: It loads the plcommpro.dll matching the current Python bitness.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import ctypes


def _python_bitness() -> str:
    return "x64" if (sys.maxsize > 2**32) else "x86"


def _pe_arch(path: Path) -> str | None:
    try:
        data = path.read_bytes()
        if len(data) < 0x40 or data[:2] != b"MZ":
            return None
        e_lfanew = int.from_bytes(data[0x3C:0x40], "little", signed=False)
        if e_lfanew + 6 >= len(data) or data[e_lfanew : e_lfanew + 4] != b"PE\0\0":
            return None
        machine = int.from_bytes(data[e_lfanew + 4 : e_lfanew + 6], "little", signed=False)
        if machine == 0x14C:
            return "x86"
        if machine == 0x8664:
            return "x64"
        return None
    except Exception:
        return None


def _default_plcommpro_dll() -> Path:
    # Allow explicit override.
    override = os.environ.get("PLCOMM_PLCOMMPRO_DLL")
    if override:
        return Path(override)

    candidates = [
        Path("Resurse/Standalone SDK-6.3.1.55/SDK/x64/plcommpro.dll"),
        Path("Resurse/Standalone SDK-6.3.1.55/SDK/x86/plcommpro.dll"),
        Path("Resurse/ZKEUBioAccessSetup/Dependencies/ZKAccess3.5/pullsdk/plcommpro.dll"),
        Path("Resurse/Standalone SDK-6.3.1.55/PullSDK/plcommpro.dll"),
        Path("Resurse/SDK-Ver2.2.0.220/plcommpro.dll"),
    ]
    existing = [p for p in candidates if p.exists()]
    if not existing:
        raise FileNotFoundError("No plcommpro.dll candidates found under Resurse/")

    target_arch = _python_bitness()
    matching = [p for p in existing if _pe_arch(p) == target_arch]
    if matching:
        return max(matching, key=lambda p: p.stat().st_size)
    return max(existing, key=lambda p: p.stat().st_size)


_dll_path = _default_plcommpro_dll()

# Ensure dependencies can be resolved.
_dll_dir = str(_dll_path.parent.resolve())
if hasattr(os, "add_dll_directory"):
    os.add_dll_directory(_dll_dir)
os.environ["PATH"] = _dll_dir + os.pathsep + os.environ.get("PATH", "")

_dll = ctypes.WinDLL(str(_dll_path.resolve()))


def Connect(conn_params: str) -> int:
    fn = _dll.Connect
    fn.argtypes = [ctypes.c_char_p]
    fn.restype = ctypes.c_int
    return int(fn(conn_params.encode("ascii", errors="ignore")))


def Disconnect(handle: int) -> int:
    fn = getattr(_dll, "Disconnect", None)
    if fn is None:
        return 0
    fn.argtypes = [ctypes.c_int]
    fn.restype = ctypes.c_int
    return int(fn(int(handle)))


def GetLastError() -> int | None:
    fn = getattr(_dll, "GetLastError", None)
    if fn is None:
        return None
    fn.argtypes = []
    fn.restype = ctypes.c_int
    return int(fn())


def PullLastError() -> int | None:
    fn = getattr(_dll, "PullLastError", None)
    if fn is None:
        return None
    fn.argtypes = []
    fn.restype = ctypes.c_int
    return int(fn())


def dll_path() -> str:
    return str(_dll_path)
