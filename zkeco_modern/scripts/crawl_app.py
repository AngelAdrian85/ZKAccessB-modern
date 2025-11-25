#!/usr/bin/env python3
import urllib.request
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser
import sys

START_URLS = ['http://127.0.0.1:8000/','http://127.0.0.1:8000/iaccess/','http://127.0.0.1:8000/registration/login/']

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag.lower()=='a':
            for k,v in attrs:
                if k.lower()=='href' and v:
                    self.links.append(v)


def same_host(url):
    p = urlparse(url)
    return p.hostname in ('127.0.0.1','localhost')

visited = set()
queue = list(START_URLS)
results = {}
max_pages = 300

while queue and len(visited) < max_pages:
    u = queue.pop(0)
    if u in visited: continue
    visited.add(u)
    try:
        r = urllib.request.urlopen(u, timeout=6)
        code = r.getcode()
        data = r.read(65536)
        text = data.decode('utf-8', errors='replace')
        parser = LinkParser()
        parser.feed(text)
        found = []
        for l in parser.links:
            absu = urljoin(u, l)
            if same_host(absu) and absu not in visited:
                found.append(absu)
                queue.append(absu)
        results[u] = {'code': code, 'links': found}
        print(f"{u} -> {code} (found {len(found)} links)")
    except Exception as e:
        results[u] = {'error': str(e)}
        print(f"{u} -> ERROR: {e}")

import json
out = Path = __import__('pathlib').Path
outp = out(__file__).resolve().parent.parent / 'reports' / 'crawl_report.json'
outp.parent.mkdir(parents=True, exist_ok=True)
outp.write_text(json.dumps(results, indent=2, ensure_ascii=False))
print('WROTE', outp)
