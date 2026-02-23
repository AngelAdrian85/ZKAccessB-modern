import json
import os
import platform
import sys
from pathlib import Path


def _p(s: str) -> None:
    print(s, flush=True)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    _p("[SMOKE] Python: " + sys.executable)
    _p("[SMOKE] Python version: " + sys.version.replace("\n", " "))
    _p("[SMOKE] Platform: " + platform.platform())
    _p("[SMOKE] CWD: " + os.getcwd())
    _p("[SMOKE] Repo root: " + str(root))

    bridge_py = os.environ.get("ZKACCESS_PYBRIDGE") or os.environ.get("ZKACCESS_PY32") or ""
    _p("[SMOKE] ZKACCESS_PYBRIDGE: " + (bridge_py or "(not set)"))

    dll_env = os.environ.get("ZKACCESS_PLCOMMPRO_DLL") or ""
    _p("[SMOKE] ZKACCESS_PLCOMMPRO_DLL: " + (dll_env or "(not set)"))

    syswow64 = Path(r"C:\Windows\SysWOW64\plcommpro.dll")
    _p(f"[SMOKE] SysWOW64 plcommpro.dll exists: {syswow64.exists()}")

    try:
        from zkeco_modern.agent.plcommpro_bridge import search_device_udp

        resp = search_device_udp()
        _p("[SMOKE] search_device_udp response:")
        _p(json.dumps(resp, ensure_ascii=False, indent=2)[:5000])

        data = (resp or {}).get("data") or ""
        _p(f"[SMOKE] data_len={len(data)}")
        if data:
            _p("[SMOKE] data_preview:")
            _p(data[:2000])

    except Exception as e:
        _p("[SMOKE] ERROR: " + repr(e))
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
