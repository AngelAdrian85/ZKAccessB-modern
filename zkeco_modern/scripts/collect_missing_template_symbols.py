"""Collect missing template filters and tags from legacy templates.

Run this script from the repo root with the Django settings env vars set.
It prints a JSON object with two lists: `filters` and `tags`.
"""
import glob
import os
import json
import re
from django.template import Template, Context, TemplateSyntaxError


def find_templates(root):
    pattern = os.path.join(root, "zkeco", "units", "adms", "mysite", "**", "templates", "**", "*.html")
    for path in glob.glob(pattern, recursive=True):
        yield path


def collect(root):
    filters = set()
    tags = set()
    msg_filter_re = re.compile(r"Invalid filter: '([A-Za-z0-9_]+)'")
    msg_tag_re = re.compile(r"Invalid block tag.*: '([A-Za-z0-9_]+)'")
    for tpl in find_templates(root):
        try:
            with open(tpl, 'r', encoding='utf-8', errors='ignore') as fh:
                src = fh.read()
            Template(src).render(Context({}))
        except TemplateSyntaxError as e:
            m1 = msg_filter_re.search(str(e))
            if m1:
                filters.add(m1.group(1))
            m2 = msg_tag_re.search(str(e))
            if m2:
                tags.add(m2.group(1))
        except Exception:
            pass
    return {'filters': sorted(filters), 'tags': sorted(tags)}


if __name__ == '__main__':
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    out = collect(repo_root)
    print(json.dumps(out, indent=2, ensure_ascii=False))
