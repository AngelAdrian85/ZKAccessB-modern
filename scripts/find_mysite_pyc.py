import sys
import os

paths = list(sys.path)
# also add some likely external locations
paths += [
    r"C:\Program Files (x86)\ZKTeco\ZKAccessB\zkeco\python-support",
    r"C:\Program Files (x86)\ZKTeco\ZKAccessB\zkeco\units\adms\mysite",
]
seen = set()
for p in paths:
    if not p or not os.path.isdir(p):
        continue
    for root, dirs, files in os.walk(p):
        if os.path.basename(root).lower() == "mysite":
            if root in seen:
                continue
            seen.add(root)
            print("Found mysite at", root)
            for f in files:
                if f.endswith(".pyc"):
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, "rb") as fh:
                            magic = fh.read(4)
                        print(" -", f, "magic=", magic)
                    except Exception as e:
                        print(" -", f, "error reading:", e)
            print()
print("Done")
