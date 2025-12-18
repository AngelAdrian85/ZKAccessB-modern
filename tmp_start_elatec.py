import json, pathlib, time, subprocess
p = pathlib.Path('tray_status.json')
st = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
# request start Elatec via cmd flag
st['cmd_start_elatec'] = True
st['cmd_start_acp'] = False
st['elatec_blocked'] = False
st['acp_blocked'] = False
p.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding='utf-8')
print('Wrote cmd_start_elatec')
# give tray_agent a moment to act
for i in range(6):
    time.sleep(1)
    print('wait', i+1)
# list processes
out = subprocess.run(['powershell','-Command', "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'card_reader_elatec.py' } | Select-Object ProcessId,CommandLine | ConvertTo-Json"], capture_output=True, text=True)
print('el_proc:', out.stdout)
# check heartbeat
hp = pathlib.Path.home()
hb = hp / 'zkeco_reader_heartbeat_elatec.json'
print('heartbeat exists', hb.exists(), 'mtime', hb.stat().st_mtime if hb.exists() else None)
# check DB
out2 = subprocess.run(['python','manage.py','shell','-c',"from agent.models import DeviceStatus; import json; qs=DeviceStatus.objects.filter(device__id__in=[3]).values('device_id','online','updated_at'); print(list(qs))"], capture_output=True, text=True)
print('db elatec:', out2.stdout)
