import sqlite3, json, sys
db='zkeco_modern/db.sqlite3'
try:
    conn=sqlite3.connect(db)
    cur=conn.cursor()
    cur.execute("SELECT d.id,d.scanner_type,ds.online FROM agent_device d JOIN agent_devicestatus ds ON ds.device_id=d.id WHERE d.scanner_type IN ('acp','elatec')")
    rows=cur.fetchall()
    print('DB_ROWS:', json.dumps(rows))
    conn.close()
except Exception as e:
    print('DB_ERROR', e)
    sys.exit(1)
