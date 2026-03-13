import json
import os
import subprocess
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .controller_decoders import parse_option_pairs


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
_OPTION_DLL_HINTS: dict[tuple[str, int, str], str] = {}
_QUERY_DLL_HINTS: dict[tuple[str, int, str, str], str] = {}


def _bridge_meta_dict(resp: Dict[str, Any]) -> dict[str, Any]:
    meta = resp.get("meta")
    return dict(meta) if isinstance(meta, dict) else {}


def _append_note_parts(*parts: Any) -> str:
    out: list[str] = []
    seen: set[str] = set()
    for part in parts:
        text = str(part or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return " | ".join(out)


def _finalize_bridge_response(
    resp: Dict[str, Any],
    *,
    request: Optional[Dict[str, Any]] = None,
    transport: str = "bridge",
) -> Dict[str, Any]:
    out = dict(resp or {})
    if request is not None:
        out.setdefault("action", str(request.get("action") or ""))
        if "dll_path_used" not in out and request.get("dll_path"):
            out["dll_path_used"] = str(request.get("dll_path") or "")
    out["action_alias"] = str(out.get("action_alias") or out.get("action") or "").strip()
    out["note"] = str(out.get("note") or "").strip()
    out["meta"] = _bridge_meta_dict(out)
    out.setdefault("transport", transport)
    return out


def _parse_option_pairs_text(raw: str) -> dict[str, str]:
    return parse_option_pairs(raw, lowercase_keys=True)


def _single_get_options_item(request: Dict[str, Any]) -> Optional[str]:
    try:
        if str(request.get("action") or "").strip().lower() != "get_options":
            return None
        items = [part.strip() for part in str(request.get("items") or "").split(",") if part.strip()]
        if len(items) != 1:
            return None
        return items[0]
    except Exception:
        return None


def _remember_option_dll_hint(request: Dict[str, Any], resp: Dict[str, Any], dll_path: str) -> None:
    item = _single_get_options_item(request)
    if not item or not dll_path:
        return
    try:
        comm = request.get("comminfo") or {}
        ip = str(comm.get("ipaddress") or "").strip()
        port = int(comm.get("ip_port") or 0)
        if (not ip) or port <= 0:
            return
        parsed = _parse_option_pairs_text(resp.get("data") or "")
        if item.strip().lower() in parsed:
            _OPTION_DLL_HINTS[(ip, port, item.strip().lower())] = str(dll_path)
    except Exception:
        return


def _query_affinity_key(request: Dict[str, Any]) -> Optional[tuple[str, int, str, str]]:
    try:
        if str(request.get("action") or "").strip().lower() != "query_data":
            return None
        comm = request.get("comminfo") or {}
        ip = str(comm.get("ipaddress") or "").strip()
        port = int(comm.get("ip_port") or 0)
        table = str(request.get("table") or "").strip().lower()
        fields = str(request.get("fields") or "*").strip().lower().replace(" ", "") or "*"
        if (not ip) or port <= 0 or table != "user":
            return None
        return (ip, port, table, fields)
    except Exception:
        return None


def _remember_query_dll_hint(request: Dict[str, Any], resp: Dict[str, Any], dll_path: str) -> None:
    key = _query_affinity_key(request)
    if key is None or not dll_path:
        return
    try:
        result = int(resp.get("result", -1) or -1)
    except Exception:
        result = -1
    text = str(resp.get("data") or "").replace("\x00", "").strip()
    if result >= 0 and text:
        _QUERY_DLL_HINTS[key] = str(dll_path)


def _preferred_plcommpro_arch() -> str:
    """Preferred plcommpro.dll architecture.

    Default is x64 because the current deployment target is 64-bit Windows.
    Operators can still force x86 for legacy SDK bundles by setting:
      ZKACCESS_PLCOMMPRO_ARCH=x86
    """
    try:
        v = str(os.environ.get("ZKACCESS_PLCOMMPRO_ARCH") or "").strip().lower()
        if v in ("x86", "32", "win-x86", "i386"):
            return "x86"
        if v in ("x64", "amd64", "64", "win-x64"):
            return "x64"
    except Exception:
        pass
    return "x64"


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

    preferred_arch = _preferred_plcommpro_arch()
    arch_order = [preferred_arch, "x86" if preferred_arch == "x64" else "x64"]

    for arch in arch_order:
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
    """Public wrapper for the best-effort default plcommpro.dll path."""
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
    item = _single_get_options_item(request)
    if ip and port:
        qhint_key = _query_affinity_key(request)
        if qhint_key is not None:
            qhint = _QUERY_DLL_HINTS.get(qhint_key)
            if qhint and _is_viable_x86_dll(qhint):
                hinted.append(qhint)
        if item:
            opt_hint = _OPTION_DLL_HINTS.get((ip, int(port), item.strip().lower()))
            if opt_hint and _is_viable_x86_dll(opt_hint):
                hinted.append(opt_hint)
        hint = _DLL_HINTS.get((ip, int(port)))
        if hint and _is_viable_x86_dll(hint):
            hinted.append(hint)

    arch = _preferred_plcommpro_arch()
    arch_order = [arch, "x86" if arch == "x64" else "x64"]
    repo: list[str] = []
    extra: list[str] = []
    sys_candidates: list[str] = []
    for current_arch in arch_order:
        if current_arch == "x64":
            repo.extend([p for p in _plcommpro_repo_candidates(arch="x64") if _is_viable_x64_dll(p)])
            extra.extend([p for p in _plcommpro_extra_dirs_candidates() if _is_viable_x64_dll(p)])
            system32 = r"C:\\Windows\\System32\\plcommpro.dll"
            if _is_viable_x64_dll(system32):
                sys_candidates.append(system32)
        else:
            repo.extend([p for p in _plcommpro_repo_candidates(arch="x86") if _is_viable_x86_dll(p)])
            extra.extend([p for p in _plcommpro_extra_dirs_candidates() if _is_viable_x86_dll(p)])
            syswow64 = r"C:\\Windows\\SysWOW64\\plcommpro.dll"
            if _is_viable_x86_dll(syswow64):
                sys_candidates.append(syswow64)

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


def _bridge_exe_path_for_arch(arch: str) -> Optional[Path]:
    try:
        base = Path(__file__).resolve().parent
        cand = base / "bridge_dotnet" / "PlcommproBridgeRunner" / "bin" / "Release" / "net8.0" / f"win-{arch}" / "publish" / "PlcommproBridgeRunner.exe"
        if cand.exists() and cand.is_file():
            return cand
    except Exception:
        pass
    return None


def _default_bridge_exe_path() -> Optional[Path]:
    """Return the preferred published plcommpro bridge executable path.

    Env `ZKACCESS_BRIDGE_EXE` still wins. Without an override we prefer the
    architecture selected by `_preferred_plcommpro_arch()`, then fall back to
    the other publish if only that one exists.
    """
    env = (os.environ.get("ZKACCESS_BRIDGE_EXE") or "").strip()
    if env:
        p = Path(env)
        try:
            if p.exists() and p.is_file() and p.suffix.lower() == ".exe":
                return p
        except Exception:
            pass

    preferred_arch = _preferred_plcommpro_arch()
    arch_order = [preferred_arch, "x86" if preferred_arch == "x64" else "x64"]
    for arch in arch_order:
        cand = _bridge_exe_path_for_arch(arch)
        if cand is not None:
            return cand
    return None


def _default_bridge_exe_path_x64() -> Optional[Path]:
    """Return a plcommpro bridge executable path (x64), if found."""
    return _bridge_exe_path_for_arch("x64")


def _default_bridge_exe_path_x86() -> Optional[Path]:
    """Return a plcommpro bridge executable path (x86), if found."""
    return _bridge_exe_path_for_arch("x86")


def _bridge_exe_for_request(request: Dict[str, Any]) -> Optional[Path]:
    """Pick the best bridge EXE for a given request.

    - If env ZKACCESS_BRIDGE_EXE is set, it always wins.
    - If request pins a dll_path, use the matching bridge bitness.
    - Otherwise, use the preferred published bridge for the current runtime.
    """

    env = (os.environ.get("ZKACCESS_BRIDGE_EXE") or "").strip()
    if env:
        p = Path(env)
        try:
            if p.exists() and p.is_file() and p.suffix.lower() == ".exe":
                # Safety: if caller pins an x64 plcommpro.dll but the env override
                # points to an x86 bridge EXE (or vice-versa), fail with a clear
                # message instead of the opaque 0x8007000B “incorrect format”.
                dll_path = str(request.get("dll_path") or "").strip()
                if dll_path and os.path.exists(dll_path):
                    try:
                        if _is_x64_pe(dll_path) and _is_x86_pe(str(p)):
                            raise PlcommproBridgeError(
                                "ZKACCESS_BRIDGE_EXE points to a 32-bit (win-x86) bridge, "
                                "but a 64-bit plcommpro.dll was pinned. "
                                "Unset ZKACCESS_BRIDGE_EXE or point it to the win-x64 publish."
                            )
                        if _is_x86_pe(dll_path) and _is_x64_pe(str(p)):
                            raise PlcommproBridgeError(
                                "ZKACCESS_BRIDGE_EXE points to a 64-bit (win-x64) bridge, "
                                "but a 32-bit plcommpro.dll was pinned. "
                                "Unset ZKACCESS_BRIDGE_EXE or point it to the win-x86 publish."
                            )
                    except PlcommproBridgeError:
                        raise
                    except Exception:
                        # If PE detection fails, still honor env override.
                        pass
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

    if dll_path and _is_x86_pe(dll_path):
        b32 = _default_bridge_exe_path_x86()
        if b32 is None:
            raise PlcommproBridgeError(
                "32-bit plcommpro.dll detected but win-x86 bridge is missing. "
                "Build it with: dotnet publish zkeco_modern/agent/bridge_dotnet/PlcommproBridgeRunner/PlcommproBridgeRunner.csproj -c Release -r win-x86"
            )
        return b32

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
        if isinstance(resp, dict):
            resp = _finalize_bridge_response(resp, request=request)
        if isinstance(resp, dict) and bool(resp.get("ok")):
            _remember_option_dll_hint(request, resp, str(resp.get("dll_path_used") or request.get("dll_path") or ""))
            _remember_query_dll_hint(request, resp, str(resp.get("dll_path_used") or request.get("dll_path") or ""))
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
        if isinstance(resp, dict):
            resp = _finalize_bridge_response(resp, request=req)
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
                _remember_option_dll_hint(req, resp, dll_path)
                _remember_query_dll_hint(req, resp, dll_path)
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
        return _finalize_bridge_response(best_ok_resp, request=request)
    return _finalize_bridge_response(last_resp, request=request)


def set_device_options(
    conn: PlcommproConnInfo,
    items: str,
    *,
    process_timeout_s: Optional[int] = None,
    dll_path: Optional[str] = None,
) -> Dict[str, Any]:
    return _run_bridge(
        {
            "action": "set_options",
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


def get_device_options(
    conn: PlcommproConnInfo,
    items: str,
    *,
    process_timeout_s: Optional[int] = None,
    dll_path: Optional[str] = None,
) -> Dict[str, Any]:
    timeout_s = process_timeout_s
    if timeout_s is None:
        try:
            timeout_ms = int(conn.timeout or 3000)
        except Exception:
            timeout_ms = 3000
        timeout_s = max(3, min(8, int((timeout_ms + 999) / 1000) + 2))
    request = {
        "action": "get_options",
        **({"process_timeout_s": int(timeout_s)} if timeout_s is not None else {}),
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
    resp = _run_bridge(request)
    requested_items = [part.strip() for part in str(items or "").split(",") if part.strip()]
    if bool(resp.get("ok")) or len(requested_items) <= 1:
        return resp

    merged: dict[str, str] = {}
    dlls: list[str] = []
    missing: list[str] = []
    affinity_hits: list[str] = []
    item_meta: dict[str, dict[str, Any]] = {}
    item_aliases: dict[str, str] = {}
    note_parts: list[str] = [str(resp.get("note") or "").strip()]
    for item in requested_items:
        single_req = dict(request)
        single_req["items"] = item
        single_resp = _run_bridge(single_req)
        item_meta[item] = _bridge_meta_dict(single_resp)
        item_aliases[item] = str(single_resp.get("action_alias") or "").strip()
        note_parts.append(str(single_resp.get("note") or "").strip())
        if not bool(single_resp.get("ok")):
            missing.append(item)
            continue
        raw = str(single_resp.get("data") or "").replace("\x00", "").strip()
        if not raw or "=" not in raw:
            missing.append(item)
            continue
        for part in [p.strip() for p in raw.split(",") if p.strip()]:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            merged[str(key or "").strip()] = str(value or "").strip()
        dll_used = str(single_resp.get("dll_path_used") or "").strip()
        if dll_used:
            dlls.append(dll_used)
        try:
            if conn.ipaddress and int(conn.ip_port or 0) > 0:
                cached = _OPTION_DLL_HINTS.get((str(conn.ipaddress).strip(), int(conn.ip_port), item.strip().lower()))
                if cached and dll_used and cached == dll_used:
                    affinity_hits.append(item)
        except Exception:
            pass

    if not merged:
        return resp

    ordered = [f"{item}={merged[item]}" for item in requested_items if item in merged]
    return {
        "ok": True,
        "result": 0,
        "data": ",".join(ordered),
        "last_error": 0,
        "action": str(request.get("action") or "get_options"),
        "action_alias": str(resp.get("action_alias") or request.get("action") or "get_options"),
        "dll_path_used": ";".join(sorted(set(dlls))),
        "partial": bool(missing),
        "missing_items": missing,
        "note": _append_note_parts(
            *note_parts,
            f"get_options fallback: item-by-item ({len(ordered)}/{len(requested_items)})",
        ),
        "dll_affinity_hits": affinity_hits,
        "meta": {
            "fallback_mode": "item-by-item",
            "requested_items": requested_items,
            "resolved_items": [item for item in requested_items if item in merged],
            "missing_items": missing,
            "dll_affinity_hits": affinity_hits,
            "item_meta": item_meta,
            "item_action_aliases": item_aliases,
        },
        "transport": "bridge",
    }


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


def get_rtlog(
    conn: PlcommproConnInfo,
    buffer_len: int = 65536,
    *,
    process_timeout_s: Optional[int] = None,
    dll_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Read real-time log via plcommpro.GetRTLog.

    Unlike GetDeviceData(table="transaction", option="NewRecord"), GetRTLog
    returns the device's real-time event buffer which includes the actual
    Wiegand card number even for unregistered / access-denied card scans.

    Returns:
        {"ok": True, "result": <event_count>, "data": "<csv_lines>"}
    """
    return _run_bridge(
        {
            "action": "get_rtlog",
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
            "buffer_len": int(buffer_len),
        }
    )


def data_count(
    conn: PlcommproConnInfo,
    table: str,
    *,
    process_timeout_s: Optional[int] = None,
    dll_path: Optional[str] = None,
) -> Dict[str, Any]:
    return _run_bridge(
        {
            "action": "data_count",
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
                retry_resp = dict(retry_resp)
                retry_resp["note"] = _append_note_parts(
                    retry_resp.get("note"),
                    f"query_data retry: user fields='*' (from {fields})",
                )
                retry_meta = _bridge_meta_dict(retry_resp)
                retry_meta.update(
                    {
                        "fallback_mode": "fields=*",
                        "original_fields": fields,
                        "retry_fields": "*",
                    }
                )
                retry_resp["meta"] = retry_meta
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


def set_device_data(
    conn: PlcommproConnInfo,
    table: str,
    data: str,
    option: str = "",
    *,
    process_timeout_s: Optional[int] = None,
    dll_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Write rows into a device table using plcommpro.SetDeviceData.

    `data` is typically a concatenation of lines separated by CRLF (\r\n), where each
    line is tab-separated key=value pairs, e.g.:
        Pin=1\tCardNo=123\tName=John

    `option` is usually empty in legacy usage.
    """
    return _run_bridge(
        {
            "action": "set_data",
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


def control_device(
    conn: PlcommproConnInfo,
    door: int,
    index: int,
    state: int,
    time: int = 0,
    *,
    process_timeout_s: Optional[int] = None,
    dll_path: Optional[str] = None,
) -> Dict[str, Any]:
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
            "door": int(door or 0),
            "index": int(index or 0),
            "state": int(state or 0),
            "time": int(time or 0),
        }
    )


def cancel_alarm(
    conn: PlcommproConnInfo,
    door: int = 0,
    *,
    process_timeout_s: Optional[int] = None,
    dll_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Cancel alarm via plcommpro.ControlDevice (op=2)."""
    return _run_bridge(
        {
            "action": "cancel_alarm",
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


def control_normal_open(
    conn: PlcommproConnInfo,
    door: int,
    state: int,
    *,
    process_timeout_s: Optional[int] = None,
    dll_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Toggle door normal-open via plcommpro.ControlDevice (op=4)."""
    return _run_bridge(
        {
            "action": "control_normal_open",
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
            "door": int(door or 0),
            "state": int(state or 0),
        }
    )
