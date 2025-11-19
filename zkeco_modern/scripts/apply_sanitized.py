import os
import json

REPORT = os.path.join(os.path.dirname(__file__), "sanitize_report.json")
LOG = os.path.join(os.path.dirname(__file__), "apply_sanitized_log.json")

if not os.path.exists(REPORT):
    print("No report found; run sanitize_fallbacks.py first")
    raise SystemExit(1)

with open(REPORT, "r", encoding="utf-8") as fh:
    report = json.load(fh)

results = {"replaced": [], "neutralized": [], "skipped": []}

def final_fallback(text: str) -> str:
    # comment out template tags and escape variable delimiters
    t = text.replace("{%", "{#").replace("%}", "#}")
    t = t.replace("{{", "&#123;&#123;").replace("}}", "&#125;&#125;")
    return t

for entry in report.get("success", []):
    src = entry.get("sanitized")
    dst = entry.get("file")
    try:
        with open(src, "r", encoding="utf-8") as fh:
            data = fh.read()
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as fh:
            fh.write(data)
        results["replaced"].append(dst)
        print("Replaced:", dst)
    except Exception as e:
        results["skipped"].append({"file": dst, "error": str(e)})

for entry in report.get("failed", []):
    part = entry.get("partial")
    dst = entry.get("file")
    if not part or not os.path.exists(part):
        results["skipped"].append({"file": dst, "error": "no partial available"})
        continue
    try:
        with open(part, "r", encoding="utf-8") as fh:
            data = fh.read()
        neut = final_fallback(data)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as fh:
            fh.write(neut)
        results["neutralized"].append(dst)
        print("Neutralized and replaced:", dst)
    except Exception as e:
        results["skipped"].append({"file": dst, "error": str(e)})

with open(LOG, "w", encoding="utf-8") as fh:
    json.dump(results, fh, ensure_ascii=False, indent=2)

print("Apply complete. Log:", LOG)
