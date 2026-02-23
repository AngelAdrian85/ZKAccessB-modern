import argparse
import os
import sys
import time
from pathlib import Path


def _filter_legacy_sys_path() -> None:
    bad_path_markers = ("ZKTeco", "python-support", "Python26")
    sys.path[:] = [
        p
        for p in sys.path
        if not (p and any(marker in p for marker in bad_path_markers))
    ]


def _default_plcommpro_dll() -> Path:
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

    # Prefer matching-arch DLL (x64 Python must load x64 DLL, etc.).
    target_arch = _python_bitness()
    matching = [p for p in existing if _pe_arch(p) == target_arch]
    if matching:
        # Prefer the largest within the matching architecture (typically the ~385KB one).
        return max(matching, key=lambda p: p.stat().st_size)

    # Fallback: largest overall.
    return max(existing, key=lambda p: p.stat().st_size)


def _pe_arch(path: Path) -> str | None:
    """Return 'x86' or 'x64' based on PE header, or None if unknown."""
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


def _python_bitness() -> str:
    return "x64" if (sys.maxsize > 2**32) else "x86"


def _load_plcommpro(dll_path: Path):
    import ctypes

    # Ensure dependencies can be resolved.
    dll_dir = str(dll_path.parent.resolve())
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(dll_dir)
    os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")

    dll = ctypes.WinDLL(str(dll_path.resolve()))

    connect = dll.Connect
    connect.argtypes = [ctypes.c_char_p]
    connect.restype = ctypes.c_int

    disconnect = getattr(dll, "Disconnect", None)
    if disconnect is not None:
        disconnect.argtypes = [ctypes.c_int]
        disconnect.restype = ctypes.c_int

    # plcommpro SDK uses PullLastError() in many builds (older code calls GetLastError()).
    pull_last_error = getattr(dll, "PullLastError", None)
    if pull_last_error is not None:
        pull_last_error.argtypes = []
        pull_last_error.restype = ctypes.c_int

    get_last_error = getattr(dll, "GetLastError", None)
    if get_last_error is not None:
        get_last_error.argtypes = []
        get_last_error.restype = ctypes.c_int

    return dll, connect, disconnect, pull_last_error, get_last_error


def _attempt(connect, pull_last_error, get_last_error, params: str):
    t0 = time.perf_counter()
    import ctypes
    ctypes.set_last_error(0)
    try:
        handle = int(connect(params.encode("ascii", errors="ignore")))
    except Exception as exc:
        return {
            "params": params,
            "handle": None,
            "last_error": None,
            "elapsed_ms": int((time.perf_counter() - t0) * 1000),
            "exception": repr(exc),
        }

    sdk_last_error = None
    if pull_last_error is not None:
        try:
            sdk_last_error = int(pull_last_error())
        except Exception:
            sdk_last_error = None
    elif get_last_error is not None:
        try:
            sdk_last_error = int(get_last_error())
        except Exception:
            sdk_last_error = None

    win_last_error = int(ctypes.get_last_error())

    return {
        "params": params,
        "handle": handle,
        "sdk_last_error": sdk_last_error,
        "win_last_error": win_last_error,
        "elapsed_ms": int((time.perf_counter() - t0) * 1000),
        "exception": None,
    }


def main() -> int:
    _filter_legacy_sys_path()

    parser = argparse.ArgumentParser(
        description="Test plcommpro Connect() directly from Python via ctypes."
    )
    parser.add_argument("--ip", default="192.168.1.235")
    parser.add_argument("--port", type=int, default=14370)
    parser.add_argument("--timeout", type=int, default=4000)
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help=(
            "Run only specific variants by label (repeatable). "
            "Example: --only passwd=888888 --only 'passwd=' --only no_passwd"
        ),
    )
    parser.add_argument(
        "--dll",
        default=None,
        help="Path to plcommpro.dll. If omitted, picks the largest candidate under Resurse/.",
    )
    args = parser.parse_args()

    if args.only:
        print(f"Only filters: {args.only}")

    dll_path = Path(args.dll) if args.dll else _default_plcommpro_dll()

    print(f"Python bitness: {_python_bitness()}")
    print(f"Using plcommpro.dll: {dll_path} (bytes={dll_path.stat().st_size})")

    dll, connect, disconnect, pull_last_error, get_last_error = _load_plcommpro(dll_path)
    print(f"Loaded from: {dll._name}")

    base = f"protocol=TCP,ipaddress={args.ip},port={args.port},timeout={args.timeout}"  # no passwd

    # Exactly the passwd variants requested by the user.
    variants = [
        ("passwd=0", f"{base},passwd=0"),
        ("passwd=12345", f"{base},passwd=12345"),
        ("passwd=123456", f"{base},passwd=123456"),
        ("passwd=5678", f"{base},passwd=5678"),
        ("passwd=888888", f"{base},passwd=888888"),
        ("passwd=", f"{base},passwd="),
        ("no_passwd", base),
    ]

    if args.only:
        only_set = set(args.only)
        variants = [v for v in variants if v[0] in only_set]
        if not variants:
            print("No variants matched --only labels.")
            return 2

    for label, params in variants:
        result = _attempt(connect, pull_last_error, get_last_error, params)
        handle = result["handle"]
        sdk_last_error = result["sdk_last_error"]
        win_last_error = result["win_last_error"]
        elapsed = result["elapsed_ms"]
        exc = result["exception"]

        print("-")
        print(f"{label}")
        print(f"  params: {params}")
        print(f"  handle: {handle}")
        print(f"  sdk_last_error: {sdk_last_error}")
        print(f"  win_last_error: {win_last_error}")
        print(f"  elapsed_ms: {elapsed}")
        if exc:
            print(f"  exception: {exc}")

        if disconnect is not None and isinstance(handle, int) and handle and handle > 0:
            try:
                disconnect(handle)
            except Exception:
                pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
