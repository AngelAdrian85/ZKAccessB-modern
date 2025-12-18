import sqlite3
from pathlib import Path
p = Path('zkeco_modern') / 'db.sqlite3'
print('DB:', p, 'exists=', p.exists())
if not p.exists():
    raise SystemExit('DB missing')
con = sqlite3.connect(str(p))
cur = con.cursor()
try:
    cur.execute('''SELECT d.id,d.name,d.scanner_type,ds.online FROM agent_device d LEFT JOIN agent_devicestatus ds ON ds.device_id=d.id WHERE d.scanner_linked=1''')
    rows = cur.fetchall()
    for r in rows:
        print(r)
except Exception as e:
    print('ERR', e)
finally:
    con.close()
