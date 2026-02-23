import json
import os
import subprocess
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


class PlcommproBridgeError(RuntimeError):
    pass


@dataclass(frozen=True)
class PlcommproConnInfo:
    ipaddress: str
    ip_port: int = 4370
    password: str = ""
    timeout: int = 3000
    comm_type: int = 1  # 1=TCP, 2=RS485
    protocol: Optional[str] = None  # e.g. 'TCP' (default) or experimental 'UDP'


_PY_BRIDGE_VALIDATED: dict[str, bool] = {}
_DLL_HINTS: dict[tuple[str, int], str] = {}


def _preferred_plcommpro_arch() -> str:
    """Preferred plcommpro.dll architecture.

    Default is x86 because legacy ZKAccessB deployments commonly ship 32-bit SDKs.
    Operators can force x64 (newer PRO panels / newer SDK drops) by setting:
      ZKACCESS_PLCOMMPRO_ARCH=x64
    """
    try:
        v = str(os.environ.get("ZKACCESS_PLCOMMPRO_ARCH") or "").strip().lower()
        if v in ("x64", "amd64", "64", "win-x64"):
            return "x64"
    except Exception:
        pass
    return "x86"


def _pe_machine(path: str) -> Optional[int]:
    """Return PE machine type for a Windows binary, if detectable."""
    try:
        p = Path(path)
        if not p.exists() or not p.is_file():
            return None
        b = p.read_bytes()
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


def _is_x86_pe(path: str) -> bool:
    # IMAGE_FILE_MACHINE_I386
    return _pe_machine(path) == 0x014C


def _is_x64_pe(path: str) -> bool:
    # IMAGE_FILE_MACHINE_AMD64
    return _pe_machine(path) == 0x8664


def _default_plcommpro_dll_path() -> Optional[str]:
    """Best-effort default for plcommpro.dll.

    We keep this lightweight and deterministic (no full-disk searches).
    Override via env ZKACCESS_PLCOMMPRO_DLL if needed.
    """

    env_path = (os.environ.get("ZKACCESS_PLCOMMPRO_DLL") or "").strip()
    if env_path and os.path.exists(env_path) and (_is_x86_pe(env_path) or _is_x64_pe(env_path)):
        return env_path

    arch = _preferred_plcommpro_arch()

    # Prefer repo-shipped DLLs first.
    # Operator tip: the *largest* bundle often includes the most complete driver set.
    # We pick the largest viable DLL among repo candidates for the selected arch.
    try:
        repo_root = Path(__file__).resolve().parents[2]
        candidates: list[Path] = []
        if arch == "x64":
            candidates = [
                repo_root / "Resurse" / "Standalone SDK-6.3.1.55" / "SDK" / "x64" / "plcommpro.dll",
            ]
        else:
            # Ordering matters: prefer legacy PullSDK / ZKAccess-bundled DLLs first.
            candidates = [
                repo_root / "Resurse" / "Standalone SDK-6.3.1.55" / "PullSDK" / "plcommpro.dll",
                repo_root / "Resurse" / "ZKEUBioAccessSetup" / "Dependencies" / "ZKAccess3.5" / "NewSDK" / "plcommpro.dll",
                repo_root / "Resurse" / "ZKEUBioAccessSetup" / "Dependencies" / "ZKAccess3.5" / "pullsdk" / "plcommpro.dll",
                repo_root / "Resurse" / "ZKEUBioAccessSetup" / "Dependencies" / "PullSDK" / "plcommpro.dll",
                repo_root / "Resurse" / "SDK-Ver2.2.0.220" / "plcommpro.dll",
                repo_root / "Resurse" / "Standalone SDK-6.3.1.55" / "SDK" / "x86" / "plcommpro.dll",
            ]
        best: tuple[int, Path] | None = None
        for c in candidates:
            try:
                is_ok = False
                if arch == "x64":
                    is_ok = c.exists() and c.is_file() and _is_x64_pe(str(c))
                else:
                    is_ok = c.exists() and c.is_file() and _is_x86_pe(str(c))

                if not is_ok:
                    continue
                size = int(c.stat().st_size or 0)
                if best is None or size > best[0]:
                    best = (size, c)
            except Exception:
                continue
        if best is not None:
            return str(best[1])
    except Exception:
        pass

    if arch == "x64":
        system32 = r"C:\\Windows\\System32\\plcommpro.dll"
        if os.path.exists(system32) and _is_x64_pe(system32):
            return system32
    else:
        syswow64 = r"C:\\Windows\\SysWOW64\\plcommpro.dll"
        if os.path.exists(syswow64) and _is_x86_pe(syswow64):
            return syswow64

    return None


def default_plcommpro_dll_path() -> Optional[str]:
    """Public wrapper for the best-effort default x86 plcommpro.dll path."""
    return _default_plcommpro_dll_path()


def _plcommpro_repo_candidates(*, arch: str) -> list[str]:
    """Known repo-shipped candidate plcommpro.dll paths (best-effort).

    Ordering matters: we keep both legacy PullSDK variants and newer SDK bundles.
    """
    try:
        repo_root = Path(__file__).resolve().parents[2]
        candidates: list[Path] = []
        if arch == "x64":
            candidates = [
                repo_root / "Resurse" / "Standalone SDK-6.3.1.55" / "SDK" / "x64" / "plcommpro.dll",
            ]
        else:
            candidates = [
                # Legacy PullSDK bundle (commonly used by older C3/F3/G)
                repo_root / "Resurse" / "Standalone SDK-6.3.1.55" / "PullSDK" / "plcommpro.dll",
                # ZKAccess3.5 bundles (often newer than Standalone PullSDK)
                repo_root / "Resurse" / "ZKEUBioAccessSetup" / "Dependencies" / "ZKAccess3.5" / "NewSDK" / "plcommpro.dll",
                repo_root / "Resurse" / "ZKEUBioAccessSetup" / "Dependencies" / "ZKAccess3.5" / "pullsdk" / "plcommpro.dll",
                repo_root / "Resurse" / "ZKEUBioAccessSetup" / "Dependencies" / "PullSDK" / "plcommpro.dll",
                # Older SDK drop
                repo_root / "Resurse" / "SDK-Ver2.2.0.220" / "plcommpro.dll",
                repo_root / "Resurse" / "Standalone SDK-6.3.1.55" / "SDK" / "x86" / "plcommpro.dll",
            ]
        return [str(p) for p in candidates]
    except Exception:
        return []


def _plcommpro_extra_dirs_candidates() -> list[str]:
    """Optional extra search roots via env.

    Env: ZKACCESS_PLCOMMPRO_DLL_DIRS=dir1;dir2;...
    We only look for a direct 'plcommpro.dll' in each folder (no recursive search).
    """
    dirs = (os.environ.get("ZKACCESS_PLCOMMPRO_DLL_DIRS") or "").strip()
    if not dirs:
        return []
    out: list[str] = []
    for raw in dirs.split(";"):
        d = (raw or "").strip().strip('"')
        if not d:
            continue
        try:
            p = Path(d)
            cand = p / "plcommpro.dll"
            if cand.exists() and cand.is_file():
                out.append(str(cand))
        except Exception:
            continue
    return out


def _is_viable_x86_dll(path: str) -> bool:
    try:
        return bool(path) and os.path.exists(path) and _is_x86_pe(path)
    except Exception:
        return False


def _is_viable_x64_dll(path: str) -> bool:
    try:
        return bool(path) and os.path.exists(path) and _is_x64_pe(path)
    except Exception:
        return False


def _dll_candidates_for_request(request: Dict[str, Any]) -> list[str]:
    """Build an ordered list of viable plcommpro.dll candidates.

    Rules:
    - If env ZKACCESS_PLCOMMPRO_DLL is set, treat it as *strict* (no fallback)
      to preserve operator intent.
    - Else, try cached per-(ip,port) hint first.
    - For non-standard / newer ports (e.g. 14370), prefer newer SDK bundles first.
    """
    action = str(request.get('action') or '').strip().lower()
    env_path = (os.environ.get("ZKACCESS_PLCOMMPRO_DLL") or "").strip()
    if env_path:
        # Treat pinned DLL as strict for connected operations, but allow best-effort
        # fallback for UDP discovery utilities (safe/read-only and helps mixed bundles).
        # Note: allow both x86 and x64 pinned DLLs; the bridge selection logic will
        # pick the matching bridge EXE based on dll_path bitness.
        if action not in ("search_device", "modify_ip"):
            if os.path.exists(env_path) and (_is_x86_pe(env_path) or _is_x64_pe(env_path)):
                return [env_path]
            return []

    ip = None
    port = None
    try:
        comm = request.get("comminfo") or {}
        ip = str(comm.get("ipaddress") or "").strip() or None
        port = int(comm.get("ip_port") or 0) or None
    except Exception:
        ip = None
        port = None

    hinted: list[str] = []
    if ip and port:
        hint = _DLL_HINTS.get((ip, int(port)))
        if hint and _is_viable_x86_dll(hint):
            hinted.append(hint)

    arch = _preferred_plcommpro_arch()
    if arch == "x64":
        repo = [p for p in _plcommpro_repo_candidates(arch="x64") if _is_viable_x64_dll(p)]
        extra = [p for p in _plcommpro_extra_dirs_candidates() if _is_viable_x64_dll(p)]
    else:
        repo = [p for p in _plcommpro_repo_candidates(arch="x86") if _is_viable_x86_dll(p)]
        extra = [p for p in _plcommpro_extra_dirs_candidates() if _is_viable_x86_dll(p)]

    # Prefer newer bundles first when using uncommon ports (common for newer panels).
    if port and int(port) not in (4370, 4371, 4372):
        preferred_prefixes = (
            os.path.join("Resurse", "Standalone SDK-6.3.1.55", "SDK"),
            os.path.join("Resurse", "ZKEUBioAccessSetup"),
            os.path.join("Resurse", "SDK-Ver2.2.0.220"),
        )
        newer: list[str] = []
        older: list[str] = []
        for p in repo:
            if any(pref in p for pref in preferred_prefixes):
                newer.append(p)
            else:
                older.append(p)
        repo = newer + older

    # Windows fallback
    sys_candidates: list[str] = []
    if arch == "x64":
        system32 = r"C:\\Windows\\System32\\plcommpro.dll"
        if _is_viable_x64_dll(system32):
            sys_candidates = [system32]
    else:
        syswow64 = r"C:\\Windows\\SysWOW64\\plcommpro.dll"
        if _is_viable_x86_dll(syswow64):
            sys_candidates = [syswow64]

    # De-duplicate while preserving order.
    ordered: list[str] = hinted + extra + repo + sys_candidates
    if env_path and _is_viable_x86_dll(env_path):
        ordered = [env_path] + ordered
    seen: set[str] = set()
    out: list[str] = []
    for p in ordered:
        if not p or p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def _search_device_output_looks_valid(data: str) -> bool:
    """Heuristic: SearchDevice output should look like key=value records."""
    try:
        s = (data or "").replace("\x00", "").strip()
        if not s:
            return False
        # Must contain key=value pairs.
        if "=" not in s:
            return False
        # Common markers across firmwares.
        markers = ("ipaddress=", "ip=", "mac=", "sn=", "serial=", "devicename=", "product=")
        sl = s.lower()
        return any(m in sl for m in markers)
    except Exception:
        return False


def _should_try_next_dll(resp: Dict[str, Any], action: str) -> bool:
    """Decide whether to retry the same request with a different DLL."""
    try:
        if bool(resp.get("ok")):
            return False
        # UDP ops can vary by SDK packaging; allow retry.
        if action in ("search_device", "modify_ip"):
            return True
        # For connected ops, only retry on connect/load-ish failures.
        result = int(resp.get("result") or 0)
        data = str(resp.get("data") or "").lower()
        # A timeout inside Connect() is frequently SDK-bundle-specific.
        # Treat as retryable so we can fall back to other plcommpro.dll variants.
        if result == -500 and ("timed out" in data or "timeout" in data):
            return True
        if "dll load failed" in data:
            return True
        if "connect failed" in data:
            return True
        if result in (-201, -2, -1):
            return True
        return False
    except Exception:
        return False


def _default_py_bridge_path() -> Optional[Path]:
    """Return a Python interpreter path intended to run the 32-bit bridge.

    We intentionally do NOT auto-fallback to legacy Python 2.6 to avoid
    polluting environments / legacy path issues.
    """
    env_candidates: list[Path] = []
    for k in ("ZKACCESS_PYBRIDGE", "ZKACCESS_PY32"):
        v = (os.environ.get(k) or "").strip()
        if v:
            env_candidates.append(Path(v))

    for p in env_candidates:
        try:
            if not p:
                continue
            if p.exists() and p.is_file() and p.suffix.lower() == ".exe":
                return p
        except Exception:
            continue
    return None


def _default_bridge_exe_path() -> Optional[Path]:
    """Return a plcommpro bridge executable path (x86), if configured or found.

    This is the preferred modern path: run an x86 helper EXE on 64-bit Windows
    to call the 32-bit plcommpro.dll without needing 32-bit Python.
    """
    env = (os.environ.get("ZKACCESS_BRIDGE_EXE") or "").strip()
    if env:
        p = Path(env)
        try:
            if p.exists() and p.is_file() and p.suffix.lower() == ".exe":
                return p
        except Exception:
            pass

    # Repo-local default (published output)
    try:
        base = Path(__file__).resolve().parent
        cand = base / "bridge_dotnet" / "PlcommproBridgeRunner" / "bin" / "Release" / "net8.0" / "win-x86" / "publish" / "PlcommproBridgeRunner.exe"
        if cand.exists() and cand.is_file():
            return cand
    except Exception:
        pass
    return None


def _default_bridge_exe_path_x64() -> Optional[Path]:
    """Return a plcommpro bridge executable path (x64), if found.

    This is used only when the caller pins a 64-bit plcommpro.dll bundle.
    """
    # Repo-local default (published output)
    try:
        base = Path(__file__).resolve().parent
        cand = (
            base
            / "bridge_dotnet"
            / "PlcommproBridgeRunner"
            / "bin"
            / "Release"
            / "net8.0"
            / "win-x64"
            / "publish"
            / "PlcommproBridgeRunner.exe"
        )
        if cand.exists() and cand.is_file():
            return cand
    except Exception:
        pass
    return None


def _bridge_exe_for_request(request: Dict[str, Any]) -> Optional[Path]:
    """Pick the best bridge EXE for a given request.

    - If env ZKACCESS_BRIDGE_EXE is set, it always wins.
    - If request pins a dll_path and it is x64, use the win-x64 bridge.
    - Otherwise, use the win-x86 bridge when available.
    """

    env = (os.environ.get("ZKACCESS_BRIDGE_EXE") or "").strip()
    if env:
        p = Path(env)
        try:
            if p.exists() and p.is_file() and p.suffix.lower() == ".exe":
                return p
        except Exception:
            pass

    dll_path = str(request.get("dll_path") or "").strip()
    if dll_path and _is_x64_pe(dll_path):
        b64 = _default_bridge_exe_path_x64()
        if b64 is None:
            raise PlcommproBridgeError(
                "64-bit plcommpro.dll detected but win-x64 bridge is missing. "
                "Build it with: dotnet publish zkeco_modern/agent/bridge_dotnet/PlcommproBridgeRunner/PlcommproBridgeRunner.csproj -c Release -r win-x64"
            )
        return b64

    return _default_bridge_exe_path()


def _bridge_script_path() -> Path:
    # Keep path stable even when CWD changes.
    return Path(__file__).resolve().parent / "bridge_py" / "plcommpro_bridge.py"


def _validate_bridge_python(py_exe: Path) -> None:
    """Ensure the interpreter is usable (Python 3.x and 32-bit)."""
    key = str(py_exe)
    if _PY_BRIDGE_VALIDATED.get(key):
        return
    try:
        cp = subprocess.run(
            [
                str(py_exe),
                "-S",
                "-c",
                "import struct,sys; print(struct.calcsize('P')*8); print(sys.version_info[0])",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            env={
                **os.environ,
                "PYTHONNOUSERSITE": "1",
                "PYTHONPATH": "",
            },
        )
        out = (cp.stdout or "").strip().splitlines()
        bits = int(out[0]) if len(out) >= 1 else 0
        major = int(out[1]) if len(out) >= 2 else 0
        if bits != 32:
            raise PlcommproBridgeError(
                f"Bridge runner must be 32-bit Python. Got {bits}-bit: {py_exe}"
            )
        if major < 3:
            raise PlcommproBridgeError(
                f"Bridge runner must be Python 3.x. Got Python {major}: {py_exe}"
            )
    except PlcommproBridgeError:
        raise
    except Exception as e:
        raise PlcommproBridgeError(f"Failed to validate bridge runner {py_exe}: {e}")
    _PY_BRIDGE_VALIDATED[key] = True


def bridge_available() -> bool:
    """Return True if a plcommpro bridge runner is available.

    Availability means either:
    - x86 bridge EXE exists (preferred), or
    - a valid 32-bit Python 3 runner is configured.
    """
    try:
        if _default_bridge_exe_path() is not None:
            return True
    except Exception:
        pass
    try:
        return _default_py_bridge_path() is not None
    except Exception:
        return False


def _run_bridge_single(request: Dict[str, Any], *, py_bridge: Optional[Path] = None) -> Dict[str, Any]:
    # Some SDK operations (large GetDeviceData buffers, SetDeviceData bulk writes)
    # can take longer on real hardware. Use a larger timeout for those.
    action = str(request.get('action') or '').strip().lower()
    timeout_s = 30
    if action in ('query_data', 'set_data'):
        timeout_s = 120
    elif action in ('delete_data', 'data_count'):
        timeout_s = 45

    # Optional per-call override (used to keep some UI actions bounded).
    try:
        override = request.get('process_timeout_s', None)
        if override is not None:
            timeout_s = max(1, int(override))
    except Exception:
        pass
    # Prefer .NET bridge EXE when available (modern path; no Python 32-bit needed).
    # If caller pins a 64-bit plcommpro.dll, auto-select the win-x64 bridge.
    bridge_exe = _bridge_exe_for_request(request)
    if bridge_exe:
        req_json = json.dumps(request, ensure_ascii=False)
        env = {
            **os.environ,
            "PYTHONNOUSERSITE": "1",
            "PYTHONPATH": "",
        }
        # Help the bridge resolve native dependencies located next to plcommpro.dll
        # (many SDK bundles ship helper DLLs in the same folder).
        try:
            dll_path = str(request.get("dll_path") or "").strip()
            dll_dir = os.path.dirname(dll_path) if dll_path else ""
            if dll_dir:
                env["PATH"] = dll_dir + os.pathsep + (env.get("PATH") or "")
        except Exception:
            pass
        try:
            cp = subprocess.run(
                [str(bridge_exe), "--request", req_json],
                capture_output=True,
                text=True,
                timeout=timeout_s,
                env=env,
            )
        except subprocess.TimeoutExpired as e:
            raise PlcommproBridgeError(f"Bridge timed out after {timeout_s}s (action={action})")

        raw = (cp.stdout or "").strip()
        if not raw:
            err = (cp.stderr or "").strip()
            raise PlcommproBridgeError(f"Bridge returned no output. stderr={err!r}")
        try:
            return json.loads(raw)
        except Exception as e:
            err = (cp.stderr or "").strip()
            raise PlcommproBridgeError(f"Bridge output not JSON: {e}. stdout={raw!r} stderr={err!r}")

    # Fallback: 32-bit Python 3 bridge script
    py_bridge = py_bridge or _default_py_bridge_path()
    if not py_bridge:
        raise PlcommproBridgeError(
            "No plcommpro bridge runner configured. "
            "Option A (recommended): build the x86 .NET bridge EXE and set env ZKACCESS_BRIDGE_EXE. "
            "Option B: install Python 3.x (32-bit) and set env ZKACCESS_PYBRIDGE (or ZKACCESS_PY32) to python.exe."
        )

    script = _bridge_script_path()
    if not script.exists():
        raise PlcommproBridgeError(f"Bridge script missing: {script}")

    _validate_bridge_python(py_bridge)

    req_json = json.dumps(request, ensure_ascii=False)

    # -S and a clean PYTHONPATH isolates us from any legacy vendor paths.
    cmd = [str(py_bridge), "-S", str(script), "--request", req_json]
    env = {
        **os.environ,
        "PYTHONNOUSERSITE": "1",
        "PYTHONPATH": "",
    }
    try:
        dll_path = str(request.get("dll_path") or "").strip()
        dll_dir = os.path.dirname(dll_path) if dll_path else ""
        if dll_dir:
            env["PATH"] = dll_dir + os.pathsep + (env.get("PATH") or "")
    except Exception:
        pass
    try:
        cp = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
        )
    except subprocess.TimeoutExpired as e:
        raise PlcommproBridgeError(f"Bridge timed out after {timeout_s}s (action={action})")

    raw = (cp.stdout or "").strip()
    if not raw:
        err = (cp.stderr or "").strip()
        raise PlcommproBridgeError(f"Bridge returned no output. stderr={err!r}")

    try:
        resp = json.loads(raw)
    except Exception as e:
        err = (cp.stderr or "").strip()
        raise PlcommproBridgeError(f"Bridge output not JSON: {e}. stdout={raw!r} stderr={err!r}")

    return resp


def _run_bridge(request: Dict[str, Any], *, py_bridge: Optional[Path] = None) -> Dict[str, Any]:
    """Run a plcommpro bridge request with best-effort DLL compatibility fallback."""

    action = str(request.get('action') or '').strip().lower()

    # If the caller explicitly pinned a DLL, do a single run.
    if "dll_path" in request:
        resp = _run_bridge_single(request, py_bridge=py_bridge)
        if isinstance(resp, dict) and "dll_path_used" not in resp:
            resp = {**resp, "dll_path_used": str(request.get("dll_path") or "")}
        return resp

    candidates = _dll_candidates_for_request(request)
    if not candidates:
        # Last resort: allow system resolution (may fail on mixed-arch systems).
        return _run_bridge_single(request, py_bridge=py_bridge)

    last_resp: Dict[str, Any] = {}
    best_ok_resp: Optional[Dict[str, Any]] = None
    comm = request.get("comminfo") or {}
    ip = str(comm.get("ipaddress") or "").strip()
    port = int(comm.get("ip_port") or 0) if str(comm.get("ip_port") or "").strip() else 0

    for idx, dll_path in enumerate(candidates):
        req = {**request, "dll_path": dll_path}
        try:
            resp = _run_bridge_single(req, py_bridge=py_bridge)
        except PlcommproBridgeError as e:
            # Important: a bad/incompatible SDK bundle can hang inside Connect().
            # Treat that as a non-fatal attempt and move on to the next DLL.
            resp = {
                "ok": False,
                "result": -500,
                "data": f"bridge_error: {e}",
                "last_error": 0,
            }
        if isinstance(resp, dict) and "dll_path_used" not in resp:
            resp = {**resp, "dll_path_used": dll_path}
        last_resp = resp

        if bool(resp.get("ok")):
            # For UDP SearchDevice, some plcommpro bundles return a non-device marker string
            # (e.g., "CallSecurityDevice") while still reporting success. Keep trying.
            if action == "search_device" and not _search_device_output_looks_valid(str(resp.get("data") or "")):
                # Treat as a non-result and try the next DLL candidate.
                if best_ok_resp is None:
                    best_ok_resp = resp
                continue
            else:
                if ip and port:
                    _DLL_HINTS[(ip, int(port))] = dll_path
                return resp

        # If it's clearly not a DLL/protocol issue, don't waste time trying all DLLs.
        if not _should_try_next_dll(resp, action):
            return resp

        # Small guard: for the most common (legacy) port, don't brute-force too many DLLs.
        if port in (4370, 4371, 4372) and idx >= 2:
            return resp

    # If no DLL produced a valid SearchDevice list, keep the first successful (even if empty/marker)
    # response to preserve legacy UX ("no devices found" vs a hard error).
    if action == "search_device" and best_ok_resp is not None:
        return best_ok_resp
    return last_resp


def set_device_options(conn: PlcommproConnInfo, items: str) -> Dict[str, Any]:
    return _run_bridge(
        {
            "action": "set_options",
            "comminfo": {
                "comm_type": conn.comm_type,
                "protocol": conn.protocol,
                "ipaddress": conn.ipaddress,
                "ip_port": int(conn.ip_port),
                "password": conn.password,
                "timeout": int(conn.timeout),
            },
            "items": items,
        }
    )


def get_device_options(
    conn: PlcommproConnInfo,
    items: str,
    *,
    process_timeout_s: Optional[int] = None,
    dll_path: Optional[str] = None,
) -> Dict[str, Any]:
    return _run_bridge(
        {
            "action": "get_options",
            **({"process_timeout_s": int(process_timeout_s)} if process_timeout_s is not None else {}),
            **({"dll_path": str(dll_path)} if dll_path else {}),
            "comminfo": {
                "comm_type": conn.comm_type,
                "protocol": conn.protocol,
                "ipaddress": conn.ipaddress,
                "ip_port": int(conn.ip_port),
                "password": conn.password,
                "timeout": int(conn.timeout),
            },
            "items": items,
        }
    )


def connect_only(
    conn: PlcommproConnInfo,
    *,
    process_timeout_s: Optional[int] = None,
    dll_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Fast SDK connectivity check (Connect + Disconnect).

    Intended for port/password validation. Uses the x86 bridge.
    """
    return _run_bridge(
        {
            "action": "connect_only",
            **({"process_timeout_s": int(process_timeout_s)} if process_timeout_s is not None else {}),
            **({"dll_path": str(dll_path)} if dll_path else {}),
            "comminfo": {
                "comm_type": conn.comm_type,
                "protocol": conn.protocol,
                "ipaddress": conn.ipaddress,
                "ip_port": int(conn.ip_port),
                "password": conn.password,
                "timeout": int(conn.timeout),
            },
        }
    )


def data_count(conn: PlcommproConnInfo, table: str, *, process_timeout_s: Optional[int] = None) -> Dict[str, Any]:
    return _run_bridge(
        {
            "action": "data_count",
            **({"process_timeout_s": int(process_timeout_s)} if process_timeout_s is not None else {}),
            "comminfo": {
                "comm_type": conn.comm_type,
                "protocol": conn.protocol,
                "ipaddress": conn.ipaddress,
                "ip_port": int(conn.ip_port),
                "password": conn.password,
                "timeout": int(conn.timeout),
            },
            "table": table,
        }
    )


def query_data(
    conn: PlcommproConnInfo,
    table: str,
    fields: str = "*",
    filter: str = "",
    option: str = "",
    buffer_len: int = 2 * 1024 * 1024,
    *,
    process_timeout_s: Optional[int] = None,
    dll_path: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "action": "query_data",
        **({"process_timeout_s": int(process_timeout_s)} if process_timeout_s is not None else {}),
        **({"dll_path": str(dll_path)} if dll_path else {}),
        "comminfo": {
            "comm_type": conn.comm_type,
            "protocol": conn.protocol,
            "ipaddress": conn.ipaddress,
            "ip_port": int(conn.ip_port),
            "password": conn.password,
            "timeout": int(conn.timeout),
        },
        "table": table,
        "fields": fields,
        "filter": filter,
        "option": option,
        "buffer_len": int(buffer_len),
    }

    resp = _run_bridge(payload)

    # C3-Pro (14370) quirk: user table rejects multi-field selection (returns -114)
    # but succeeds with fields='*'. Keep callers stable by retrying once.
    try:
        if (
            not bool(resp.get("ok"))
            and str(table or "").strip().lower() == "user"
            and str(fields or "").strip() != "*"
            and "," in str(fields or "")
            and int(resp.get("result") or 0) == -114
        ):
            retry_payload = dict(payload)
            retry_payload["fields"] = "*"
            retry_resp = _run_bridge(retry_payload)
            if isinstance(retry_resp, dict):
                retry_resp.setdefault("note", f"query_data retry: user fields='*' (from {fields})")
            return retry_resp
    except Exception:
        pass

    return resp


def delete_device_data(
    conn: PlcommproConnInfo,
    table: str,
    filter: str = "",
    *,
    process_timeout_s: Optional[int] = None,
    dll_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Delete data rows from a device table using plcommpro.DeleteDeviceData.

    Legacy semantics (ZKAccess): used by "Clear Data in the Device when Adding"
    to clear *non-event* data. Do NOT call this on the event log table unless
    explicitly intended.
    """
    return _run_bridge(
        {
            "action": "delete_data",
            **({"process_timeout_s": int(process_timeout_s)} if process_timeout_s is not None else {}),
            **({"dll_path": str(dll_path)} if dll_path else {}),
            "comminfo": {
                "comm_type": conn.comm_type,
                "protocol": conn.protocol,
                "ipaddress": conn.ipaddress,
                "ip_port": int(conn.ip_port),
                "password": conn.password,
                "timeout": int(conn.timeout),
            },
            "table": table,
            "filter": filter,
        }
    )


def set_device_data(conn: PlcommproConnInfo, table: str, data: str, option: str = "") -> Dict[str, Any]:
    """Write rows into a device table using plcommpro.SetDeviceData.

    `data` is typically a concatenation of lines separated by CRLF (\r\n), where each
    line is tab-separated key=value pairs, e.g.:
        Pin=1\tCardNo=123\tName=John

    `option` is usually empty in legacy usage.
    """
    return _run_bridge(
        {
            "action": "set_data",
            "comminfo": {
                "comm_type": conn.comm_type,
                "protocol": conn.protocol,
                "ipaddress": conn.ipaddress,
                "ip_port": int(conn.ip_port),
                "password": conn.password,
                "timeout": int(conn.timeout),
            },
            "table": table,
            "data": data,
            "option": option,
        }
    )


def enable_device(
    conn: PlcommproConnInfo,
    enable: int,
    *,
    process_timeout_s: Optional[int] = None,
    dll_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Enable/disable a device via plcommpro.EnableDevice.

    Many ZKTeco panels require the device to be disabled (enable=0) while
    updating personnel tables (e.g. 'user').
    """
    return _run_bridge(
        {
            "action": "enable_device",
            **({"process_timeout_s": int(process_timeout_s)} if process_timeout_s is not None else {}),
            **({"dll_path": str(dll_path)} if dll_path else {}),
            "comminfo": {
                "comm_type": conn.comm_type,
                "protocol": conn.protocol,
                "ipaddress": conn.ipaddress,
                "ip_port": int(conn.ip_port),
                "password": conn.password,
                "timeout": int(conn.timeout),
            },
            "enable": int(enable),
        }
    )


def search_device_udp(address: Optional[str] = None) -> Dict[str, Any]:
    """Legacy-equivalent discovery via UDP broadcast (plcommpro.SearchDevice).

    Some networks block global broadcast (255.255.255.255). When possible, pass a
    directed broadcast like 192.168.1.255.
    """
    addr = (address or "").strip() or "255.255.255.255"
    return _run_bridge({"action": "search_device", "address": addr})


def modify_ip_udp(payload: str, address: Optional[str] = None) -> Dict[str, Any]:
    """Legacy-equivalent IP change via UDP broadcast (plcommpro.ModifyIPAddress).

    Payload is a plcommpro SDK buffer string, typically:
    MAC=xx:xx:xx:xx:xx:xx,IPAddress=...,NetMask=...,GATEIPAddress=...
    """
    addr = (address or "").strip() or "255.255.255.255"
    return _run_bridge({"action": "modify_ip", "payload": payload, "address": addr})


def control_device(conn: PlcommproConnInfo, door: int, index: int, state: int, time: int = 0) -> Dict[str, Any]:
    """Control door relay via plcommpro.ControlDevice (op=1).

    Legacy semantics:
      ControlDevice(handle, 1, door, index, state, time, '')

    Typical usage:
      - Open:  index=1, state=1
      - Close: index=1, state=0
    """
    return _run_bridge(
        {
            "action": "control_device",
            "comminfo": {
                "comm_type": conn.comm_type,
                "protocol": conn.protocol,
                "ipaddress": conn.ipaddress,
                "ip_port": int(conn.ip_port),
                "password": conn.password,
                "timeout": int(conn.timeout),
            },
            "door": int(door or 0),
            "index": int(index or 0),
            "state": int(state or 0),
            "time": int(time or 0),
        }
    )


def cancel_alarm(conn: PlcommproConnInfo, door: int = 0) -> Dict[str, Any]:
    """Cancel alarm via plcommpro.ControlDevice (op=2)."""
    return _run_bridge(
        {
            "action": "cancel_alarm",
            "comminfo": {
                "comm_type": conn.comm_type,
                "protocol": conn.protocol,
                "ipaddress": conn.ipaddress,
                "ip_port": int(conn.ip_port),
                "password": conn.password,
                "timeout": int(conn.timeout),
            },
            "door": int(door or 0),
        }
    )


def reboot_device(conn: PlcommproConnInfo) -> Dict[str, Any]:
    """Reboot device via plcommpro.ControlDevice (op=3)."""
    return _run_bridge(
        {
            "action": "reboot",
            "comminfo": {
                "comm_type": conn.comm_type,
                "protocol": conn.protocol,
                "ipaddress": conn.ipaddress,
                "ip_port": int(conn.ip_port),
                "password": conn.password,
                "timeout": int(conn.timeout),
            },
        }
    )


def control_normal_open(conn: PlcommproConnInfo, door: int, state: int) -> Dict[str, Any]:
    """Toggle door normal-open via plcommpro.ControlDevice (op=4)."""
    return _run_bridge(
        {
            "action": "control_normal_open",
            "comminfo": {
                "comm_type": conn.comm_type,
                "protocol": conn.protocol,
                "ipaddress": conn.ipaddress,
                "ip_port": int(conn.ip_port),
                "password": conn.password,
                "timeout": int(conn.timeout),
            },
            "door": int(door or 0),
            "state": int(state or 0),
        }
    )
