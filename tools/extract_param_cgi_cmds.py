import re
import ssl
import urllib.request

ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
u = "https://192.168.1.235/js/common.js"
req = urllib.request.Request(u, headers={"User-Agent": "zkprobe"})
with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
    data = r.read().decode("utf-8", "replace")

# Find blocks that mention param.cgi, then extract cmd values within ~300 chars
cmds = set()
for m in re.finditer(r"param\.cgi", data):
    start = max(0, m.start() - 300)
    end = min(len(data), m.end() + 300)
    chunk = data[start:end]
    for c in re.findall(r"\"cmd\"\s*:\s*\"([^\"]+)\"", chunk):
        cmds.add(c)

print("param.cgi cmds (from common.js):")
for c in sorted(cmds):
    print(" ", c)
