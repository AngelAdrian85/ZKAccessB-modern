import json, time, pathlib, subprocess
p = pathlib.Path('tray_status.json')
try:
    st = json.loads(p.read_text(encoding='utf-8'))
except Exception:
    st = {}
# Stop all
st.update({'acp_blocked': True, 'elatec_blocked': True, 'acp':'OPRIT', 'elatec':'OPRIT', 'cmd_stop_acp': True, 'cmd_stop_elatec': True})
p.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding='utf-8')
print('Wrote stop flags')
# wait for tray_agent to act
for i in range(12):
    time.sleep(1)
    print('wait', i+1)
# inspect processes
out = subprocess.run(['powershell','-Command', "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'card_reader_acp.py|card_reader_elatec.py' } | Select-Object ProcessId,CommandLine | ConvertTo-Json"], capture_output=True, text=True)
print('processes:', out.stdout[:2000])
# inspect DB
out2 = subprocess.run(['python','manage.py','shell','-c',"from agent.models import DeviceStatus; import json; qs=DeviceStatus.objects.filter(device__id__in=[2,3]).values('device_id','online','updated_at'); print(list(qs))"], capture_output=True, text=True)
print('db:', out2.stdout)
# Now Start all
st.update({'acp_blocked': False, 'elatec_blocked': False, 'cmd_start_acp': True, 'cmd_start_elatec': True, 'acp':'PORNESTE', 'elatec':'PORNESTE'})
p.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding='utf-8')
print('Wrote start flags')
for i in range(8):
    time.sleep(1)
    print('start wait', i+1)
out = subprocess.run(['powershell','-Command', "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'card_reader_acp.py|card_reader_elatec.py' } | Select-Object ProcessId,CommandLine | ConvertTo-Json"], capture_output=True, text=True)
print('processes after start:', out.stdout[:2000])
out2 = subprocess.run(['python','manage.py','shell','-c',"from agent.models import DeviceStatus; import json; qs=DeviceStatus.objects.filter(device__id__in=[2,3]).values('device_id','online','updated_at'); print(list(qs))"], capture_output=True, text=True)
print('db after start:', out2.stdout)
