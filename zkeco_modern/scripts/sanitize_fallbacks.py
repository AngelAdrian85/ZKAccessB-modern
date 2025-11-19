import os
import re
import json
try:
    import django
    from django.template import Template, Context, TemplateSyntaxError
except Exception:
    django = None
    Template = None
    Context = None
    TemplateSyntaxError = None


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FALLBACK_LIST = os.path.join(os.path.dirname(__file__), "final_fallback.txt")
OUT_DIR = os.path.join(os.path.dirname(__file__), "sanitized")
REPORT = os.path.join(os.path.dirname(__file__), "sanitize_report.json")


def _repair_blocks(text: str):
    tag_re = re.compile(r"{%\s*([^\s%]+)([^%]*)%}")
    openers = {"if", "for", "block"}
    middle_tags = {"else", "elif", "empty"}
    parts = []
    last = 0
    stack = []
    for m in tag_re.finditer(text):
        parts.append(text[last:m.start()])
        tag_name = m.group(1).lower()
        full = m.group(0)
        if tag_name in openers:
            stack.append(tag_name)
            parts.append(full)
        elif tag_name in middle_tags:
            parts.append(full)
        elif tag_name.startswith("end"):
            end_name = tag_name[3:]
            if stack:
                top = stack[-1]
                if end_name == top:
                    stack.pop()
                    parts.append(full)
                else:
                    if end_name in openers and top in openers:
                        fixed = re.sub(r"^{%\s*end[^\s%]+", "{% end" + top, full, flags=re.I)
                        parts.append(fixed)
                        stack.pop()
                    else:
                        parts.append(full)
            else:
                parts.append(full)
        else:
            parts.append(full)
        last = m.end()
    parts.append(text[last:])
    if stack:
        for opener in reversed(stack):
            parts.append("{% end" + opener + " %}")
    return "".join(parts)


def _fix_tokens(src: str) -> str:
    # neutralize script blocks
    def _script_repl(m):
        body = m.group(1)
        safe = body.replace("{{", "&#123;&#123;").replace("{%", "&#123;%")
        return "<script>" + safe + "</script>"

    src = re.sub(r"<script[^>]*>(.*?)</script>", _script_repl, src, flags=re.S | re.I)
    # collapse stray braces inside tokens and quote simple filter args
    src = re.sub(r"(['\"]?\})(\{\{|\{% )", r"\1 \2", src)
    src = re.sub(r"\|([A-Za-z0-9_]+)\s+([A-Za-z0-9_./%-]+)", r"|\1:'\2'", src)
    # token-scoped interior fixes
    src = re.sub(r"{%\s*(.*?)\s*%}", lambda m: "{% " + re.sub(r"}\s*", " ", m.group(1)).replace('}', ' ').strip() + " %}", src, flags=re.S)
    src = re.sub(r"{{\s*(.*?)\s*}}", lambda m: "{{ " + re.sub(r"}\s*", " ", m.group(1)).replace('}', ' ').strip() + " }}", src, flags=re.S)
    return src


def sanitize_and_try(path: str):
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        src = fh.read()
    src2 = _repair_blocks(src)
    src2 = _fix_tokens(src2)
    # final attempt: try rendering
    # If Django template engine is importable and configured, try to
    # render to validate. Otherwise just return the sanitized text and
    # mark parsing as skipped.
    if Template is None:
        return None, src2, "parsing_skipped"
    try:
        # Ensure Django apps are loaded if possible (needed for some tags/filters)
        if django is not None:
            try:
                django.setup()
            except Exception:
                # ignore setup errors; we'll try rendering anyway
                pass
        Template(src2).render(Context({}))
        return True, src2, None
    except TemplateSyntaxError as e:
        # Try an automatic, conservative repair loop for common mismatched end-tags.
        msg = str(e)
        src_lines = src2.splitlines(True)
        # Attempt small number of automatic repairs (line-based replacement)
        for _ in range(5):
            m = re.search(r"Invalid block tag on line (\d+): '([^']+)', expected (.+?)\\.", msg)
            if not m:
                break
            line_no = int(m.group(1)) - 1
            offending = m.group(2)
            expected_raw = m.group(3)
            candidates = [s.strip().strip("'") for s in re.split(r" or ", expected_raw)]
            chosen = None
            for c in candidates:
                if c.startswith('end'):
                    chosen = c
                    break
            if not chosen and candidates:
                chosen = 'end' + candidates[0]

            if chosen is None:
                break

            # replace offending tag occurrence on the reported line
            if 0 <= line_no < len(src_lines):
                line = src_lines[line_no]
                pattern = re.compile(r"({%\s*)" + re.escape(offending) + r"(\b[^%}]*)(%})", flags=re.I)
                new_line, nsub = pattern.subn(r"\1" + chosen + r" \3", line, count=1)
                if nsub:
                    src_lines[line_no] = new_line
                    src2 = ''.join(src_lines)
                    try:
                        Template(src2).render(Context({}))
                        return True, src2, None
                    except TemplateSyntaxError as e2:
                        msg = str(e2)
                        continue
                    except Exception as e2:
                        return None, src2, f"parsing_error: {e2}"
            break
        return False, src2, str(e)
    except Exception as e:
        # If Django settings or template engine can't be instantiated
        # treat as parsing skipped/error and continue.
        return None, src2, f"parsing_error: {e}"


def main():
    results = {"processed": [], "success": [], "failed": []}
    if not os.path.exists(FALLBACK_LIST):
        print("No final_fallback.txt found; nothing to sanitize.")
        return
    with open(FALLBACK_LIST, "r", encoding="utf-8") as fh:
        lines = [l.strip() for l in fh if l.strip()]

    for full in lines:
        results["processed"].append(full)
        if not os.path.exists(full):
            results["failed"].append({"file": full, "error": "missing file"})
            continue
        ok, sanitized, err = sanitize_and_try(full)
        rel = os.path.relpath(full, REPO_ROOT)
        outpath = os.path.join(OUT_DIR, rel)
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        if ok:
            with open(outpath, "w", encoding="utf-8") as fh:
                fh.write(sanitized)
            results["success"].append({"file": full, "sanitized": outpath})
        else:
            # write partial sanitized for inspection
            with open(outpath + ".partial.html", "w", encoding="utf-8") as fh:
                fh.write(sanitized)
            results["failed"].append({"file": full, "error": err, "partial": outpath + ".partial.html"})

    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)
    print("Sanitization complete. Report:", REPORT)


if __name__ == '__main__':
    main()
