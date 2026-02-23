import ssl
import urllib.request

ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
u = "https://192.168.1.235/js/common.js"
req = urllib.request.Request(u, headers={"User-Agent": "zkprobe"})
with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
    data = r.read().decode("utf-8", "replace")

lines = data.splitlines()
hit_idxs = [i for i,l in enumerate(lines) if "param.cgi" in l]
for i in hit_idxs[:40]:
    start = max(0, i-3)
    end = min(len(lines), i+4)
    print(f"--- lines {start+1}-{end} ---")
    for j in range(start, end):
        print(f"{j+1:04d}: {lines[j]}")
