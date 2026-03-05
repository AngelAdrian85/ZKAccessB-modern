"""Test all possible table names and options to find card number for unenrolled cards.
Also check device parameters that may affect card number reporting.
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'zkeco_config.settings'
import django; django.setup()

from agent.drivers.plcommpro_bridge_driver import PlcommproBridgeDriver
from agent.models import Device

dev = Device.objects.get(pk=22)
drv = PlcommproBridgeDriver(dev)

print(f"=== Device: {dev.ip_address}:{dev.port} ===")
print()

# Scan your card during this script!
print("SCANEAZA CARDUL ACUM! (astept 15 secunde inainte de a incepe testele)")
time.sleep(15)

# 1. Check key device parameters that affect card reporting
PARAM_KEYS = (
    "CardAutoAdd,CardFmt,CardBitLen,WiegandFmtDef,WGFailedId,WGSiteCode,"
    "RFCardOn,OEMCode,RealTimeMonitor,CardViewMode,CardSendFullNo,"
    "RS232BaudRate,IPAddress,NetMask,GATEIPAddress,Wiegand"
)
print("=== Device Parameters ===")
r = drv.query_data.__func__(drv, table='options') if False else drv._with_password_fallback(
    lambda c: __import__('agent.plcommpro_bridge', fromlist=['get_device_options']).get_device_options(c, PARAM_KEYS)
)
if r.get('ok'):
    print("Options:", r.get('data',''))
else:
    # try via get_options
    from agent.plcommpro_bridge import PlcommproConnInfo, get_device_options
    conn = PlcommproConnInfo(ipaddress=dev.ip_address, ip_port=dev.port, password=dev.comm_password or '0')
    r2 = get_device_options(conn, PARAM_KEYS)
    print("Options result:", r2.get('result'), r2.get('data', '')[:500])
    # Try each individually
    for k in ['CardAutoAdd','CardFmt','CardBitLen','WiegandFmtDef','WGFailedId','CardSendFullNo','OEMCode','RFCardOn']:
        r3 = get_device_options(conn, k)
        if r3.get('ok'):
            print(f"  {k} = {r3.get('data','')}")

print()

# 2. Try all possible table names
TABLE_NAMES = ['wiegand', 'oplog', 'exlogdata', 'alarmlog', 'failedlog', 'rfcardlog', 'cardlog',
               'newlog', 'realtime', 'rtlog', 'accesslog', 'accessRecord', 'cardRecord']
print("=== Table scan (NewRecord) ===")
for tbl in TABLE_NAMES:
    r = drv.query_data(table=tbl, fields='*', option='NewRecord')
    result = r.get('result', -99)
    data = r.get('data', '')
    lines = [l.strip() for l in data.replace('\r\n', '\n').split('\n') if l.strip()]
    print(f"  table={tbl!r:20s}  result={result:4d}  lines={len(lines):3d}  preview={repr(data[:80])}")

print()

# 3. Try transaction with KeepData (history)
print("=== transaction KeepData (last 100) ===")
r = drv.query_data(table='transaction', fields='*', option='KeepData')
print("  result:", r.get('result'))
data = r.get('data', '')
lines = [l.strip() for l in data.replace('\r\n', '\n').split('\n') if l.strip()]
print("  lines:", len(lines))
for ln in lines[-10:]:
    print("  LINE:", repr(ln))

print()

# 4. GetRTLog one more time
print("=== GetRTLog right now ===")
r = drv.get_rtlog()
print("  result:", r.get('result'))
data = r.get('data', '')
for ln in data.replace('\r\n', '\n').split('\n'):
    ln = ln.strip()
    if ln:
        print("  RTLog:", repr(ln))

print()
print("Done.")
