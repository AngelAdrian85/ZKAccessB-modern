import ssl
import urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

u = "https://192.168.1.235/js/login.js"
print("fetch", u)
req = urllib.request.Request(u, headers={"User-Agent": "zkprobe"})
with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
    data = r.read().decode("utf-8", "replace")
print("len", len(data))

needles = ("login.cgi", "userpass", "username", "Base64", "md5", "hex_md5")
for line in data.splitlines():
    if any(n in line for n in needles):
        if len(line) > 500:
            line = line[:500] + "..."
        print(line)
