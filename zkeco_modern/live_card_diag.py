"""Live diagnostic: poll GetRTLog and transaction every 1s, print any new line found."""
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'zkeco_config.settings'

import django
django.setup()

from agent.drivers.plcommpro_bridge_driver import PlcommproBridgeDriver
from agent.models import Device

dev = Device.objects.get(pk=22)
drv = PlcommproBridgeDriver(dev)

print(f"Device: {dev.ip_address}:{dev.port}")
print("=" * 60)
print("GATA - scaneaza cardul la centrala acum!")
print("Polling GetRTLog + transaction la fiecare 1 secunda...")
print("=" * 60)
sys.stdout.flush()

seen = set()

for i in range(120):
    timestamp = time.strftime('%H:%M:%S')

    # --- GetRTLog ---
    try:
        r = drv.get_rtlog()
        data = r.get('data', '')
        for ln in data.replace('\r\n', '\n').split('\n'):
            ln = ln.strip()
            if not ln:
                continue
            if ln.lower().replace(' ', '').startswith('pin,verified'):
                continue  # header only
            if ln in seen:
                continue
            seen.add(ln)
            parts = [p.strip() for p in ln.split(',')]
            print(f"[{timestamp}] GetRTLog RAW: {repr(ln)}")
            if len(parts) >= 8:
                print(f"   pin=[{parts[0]}]  verified=[{parts[1]}]  door=[{parts[2]}]  eventType=[{parts[3]}]  time=[{parts[5]}]  index=[{parts[6]}]  cardno=[{parts[7]}]")
            elif len(parts) >= 6:
                print(f"   pin=[{parts[0]}]  verified=[{parts[1]}]  door=[{parts[2]}]  eventType=[{parts[3]}]  inOut=[{parts[4]}]  time=[{parts[5]}]")
            sys.stdout.flush()
    except Exception as e:
        print(f"[{timestamp}] GetRTLog error: {e}")

    # --- transaction NewRecord with explicit fields (Cardno first) ---
    try:
        r2 = drv.query_data(
            table='transaction',
            fields='Cardno,Pin,Verified,DoorID,EventType,InOutState,Time_second',
            option='NewRecord'
        )
        data2 = r2.get('data', '')
        for ln2 in data2.replace('\r\n', '\n').split('\n'):
            ln2 = ln2.strip()
            if not ln2:
                continue
            llow = ln2.lower().replace(' ', '')
            if llow.startswith('cardno') or llow.startswith('pin,'):
                continue  # header
            if ln2 in seen:
                continue
            seen.add(ln2)
            parts2 = [p.strip() for p in ln2.split(',')]
            print(f"[{timestamp}] TXN (Cardno-first) RAW: {repr(ln2)}")
            if len(parts2) >= 7:
                print(f"   cardno=[{parts2[0]}]  pin=[{parts2[1]}]  verified=[{parts2[2]}]  door=[{parts2[3]}]  eventType=[{parts2[4]}]  time=[{parts2[6]}]")
            sys.stdout.flush()
    except Exception as e:
        print(f"[{timestamp}] TXN error: {e}")

    # --- transaction wildcard KeepData (full history) every 10s ---
    if i % 10 == 0:
        try:
            r3 = drv.query_data(table='transaction', fields='*', option='KeepData')
            data3 = r3.get('data', '')
            lines3 = [l.strip() for l in data3.replace('\r\n', '\n').split('\n') if l.strip()]
            new_count = sum(1 for l in lines3 if l not in seen and not l.lower().startswith('pin'))
            print(f"[{timestamp}] TXN KeepData: {len(lines3)} total lines, {new_count} new")
            for ln3 in lines3:
                if ln3 in seen:
                    continue
                seen.add(ln3)
                if ln3.lower().replace(' ', '').startswith('pin,'):
                    continue
                parts3 = [p.strip() for p in ln3.split(',')]
                print(f"  KeepData LINE: {repr(ln3)}")
                if len(parts3) >= 8:
                    print(f"    pin=[{parts3[0]}]  cardno=[{parts3[7]}]  door=[{parts3[2]}]  evt=[{parts3[3]}]")
            sys.stdout.flush()
        except Exception as e:
            print(f"[{timestamp}] TXN KeepData error: {e}")

    time.sleep(1)

print("Terminat.")
