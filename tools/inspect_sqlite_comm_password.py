from __future__ import annotations

import sqlite3
from pathlib import Path


def main() -> int:
    db = Path(__file__).resolve().parents[1] / "zkeco_modern" / "db_backup_before_fix_20251218.sqlite3"
    if not db.exists():
        print(f"DB not found: {db}")
        return 2

    con = sqlite3.connect(str(db))
    cur = con.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cur.fetchall()}

    candidates = [
        "agent_device",
        "device",
        "iclock_device",
        "iaccess_device",
        "devices_device",
        "agent_devices",
    ]

    found_any = False
    for t in candidates:
        if t not in tables:
            continue
        cur.execute(f"PRAGMA table_info({t})")
        cols = [r[1] for r in cur.fetchall()]
        pw_col = None
        for k in ("comm_password", "commkey", "comm_pwd", "passwd", "password"):
            if k in cols:
                pw_col = k
                break
        if not pw_col:
            continue

        found_any = True
        print(f"table={t} pw_col={pw_col}")
        select_cols = [c for c in ("id", "name", "ip_address", "port", pw_col) if c in cols]
        cur.execute(f"SELECT {', '.join(select_cols)} FROM {t} LIMIT 20")
        rows = cur.fetchall()
        for row in rows[:10]:
            print("  ", row)

    if not found_any:
        print("No obvious device password columns found in common tables.")

    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
