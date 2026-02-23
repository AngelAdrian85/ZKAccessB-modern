from __future__ import annotations

import configparser
from pathlib import Path

p = Path.home() / "zkeco_tray_config.ini"
print("home:", Path.home())
print("config:", p)
print("exists:", p.exists())
if p.exists():
    print("first20 bytes:", p.read_bytes()[:20])

cp = configparser.ConfigParser()
try:
    cp.read(p, encoding="utf-8")
    print("read: ok")
except Exception as e:
    print("read: error", repr(e))

print("sections:", cp.sections())
print("tray.port:", cp.get("tray", "port", fallback="(missing)"))
print("tray.server_mode:", cp.get("tray", "server_mode", fallback="(missing)"))
