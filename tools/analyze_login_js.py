import ssl
import urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

u = "https://192.168.1.235/js/login.js"
req = urllib.request.Request(u, headers={"User-Agent": "zkprobe"})
with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
    data = r.read().decode("utf-8", "replace")

lines = data.splitlines()

needles = ("login.cgi", "cmd=", "ajaxUrl", "base64", "md5", "-username", "-userpass")

hits = [i for i, line in enumerate(lines) if any(n in line for n in needles)]
seen = set()
for i in hits:
    # Print a small window for each hit, de-duplicated
    start = max(0, i - 3)
    end = min(len(lines), i + 4)
    key = (start, end)
    if key in seen:
        continue
    seen.add(key)
    print(f"--- lines {start+1}-{end} ---")
    for j in range(start, end):
        print(f"{j+1:04d}: {lines[j]}")
