#!/usr/bin/env python3
"""Auto-apply heuristic fixes to failed validated partials.

Reads `validation_report.json` and for each failed entry applies targeted
heuristic fixes based on the error message, writes the modified partial back,
and prints a summary. Designed to be conservative: it only performs small
textual replacements (swap endif<->endblock, remove `{% load i18n %}`,
inline simple `{% trans "..." %}` usages).

Run from repository root using the same Python environment used for validation.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'zkeco_modern' / 'scripts'
REPORT = SCRIPTS / 'validation_report.json'


def inline_transitions(text: str) -> str:
    # remove load i18n
    text = re.sub(r"{%\s*load\s+i18n\s*%}\n?", "", text)
    # replace simple {% trans "..." %} with the quoted content
    text = re.sub(r"{%\s*trans\s+\"([^\"]+)\"\s*%}", lambda m: m.group(1), text)
    text = re.sub(r"{%\s*trans\s+'([^']+)'\s*%}", lambda m: m.group(1), text)
    return text


def replace_tag_at_line(lines, lineno, old_tag, new_tag):
    idx = lineno - 1
    if idx < 0 or idx >= len(lines):
        return False
    line = lines[idx]
    if old_tag in line:
        lines[idx] = line.replace(old_tag, new_tag, 1)
        return True
    # fallback: search nearby lines (±3)
    for d in range(1, 4):
        for i in (idx - d, idx + d):
            if 0 <= i < len(lines) and old_tag in lines[i]:
                lines[i] = lines[i].replace(old_tag, new_tag, 1)
                return True
    return False


def process_failure(entry):
    partial = Path(entry['partial'])
    if not partial.exists():
        return False, 'partial_missing'
    txt = partial.read_text(encoding='utf-8')
    orig = txt

    # quick i18n fixes if translation infra reported
    err = entry.get('error', '')
    if 'translation infrastructure' in err or "Unknown argument for 'trans'" in err or "trans' tag" in err:
        txt = inline_transitions(txt)

    # Try to parse line number from message
    m = re.search(r'on line (\d+):.*expected \'([^\']+)\'.*got \'([^\']+)\'', err)
    if not m:
        # Some messages are like: "Invalid block tag on line 83: 'endfor', expected 'endblock'."
        m2 = re.search(r"on line (\d+): '([^']+)', expected '([^']+)'", err)
        if m2:
            lineno = int(m2.group(1))
            found = m2.group(2)
            expected = m2.group(3)
        else:
            lineno = None
            found = None
            expected = None
    else:
        lineno = int(m.group(1))
        expected = m.group(2)
        found = m.group(3)

    lines = txt.splitlines()
    changed = False

    if lineno and found and expected:
        # common swap: found 'endif' expected 'endblock' => change that endif -> endblock
        if found == 'endif' and expected == 'endblock':
            if replace_tag_at_line(lines, lineno, '{% endif %}', '{% endblock %}'):
                changed = True
        elif found == 'endblock' and expected == 'endif':
            if replace_tag_at_line(lines, lineno, '{% endblock %}', '{% endif %}'):
                changed = True
        elif found == 'endfor' and expected == 'endblock':
            if replace_tag_at_line(lines, lineno, '{% endfor %}', '{% endblock %}'):
                changed = True
        elif found == 'endif' and expected in ('empty', 'endfor'):
            # likely an {% empty %} or {% endfor %} mismatch inside for loop
            if replace_tag_at_line(lines, lineno, '{% endif %}', '{% endfor %}'):
                changed = True

    # aggressive fallback: if still contains '{% load i18n %}' or '{% trans' replace them
    joined = "\n".join(lines)
    new_joined = inline_transitions(joined)
    if new_joined != joined:
        lines = new_joined.splitlines()
        changed = True

    if changed:
        partial.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        return True, 'patched'

    return False, 'no_change'


def main():
    if not REPORT.exists():
        print('Missing validation report:', REPORT)
        return 2
    data = json.loads(REPORT.read_text(encoding='utf-8'))
    failed = data.get('failed', [])
    results = []
    for ent in failed:
        ok, reason = process_failure(ent)
        results.append({'partial': ent.get('partial'), 'file': ent.get('file'), 'result': reason})

    out = SCRIPTS / 'auto_fix_results.json'
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Wrote auto-fix results to', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
