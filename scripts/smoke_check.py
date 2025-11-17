import sys
from urllib.request import urlopen
from html.parser import HTMLParser

class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ''
    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'title':
            self.in_title = True
    def handle_endtag(self, tag):
        if tag.lower() == 'title':
            self.in_title = False
    def handle_data(self, data):
        if self.in_title:
            self.title += data

urls = ['http://127.0.0.1:8000/', 'http://127.0.0.1:8000/admin/']

for u in urls:
    try:
        resp = urlopen(u, timeout=5)
        code = resp.getcode()
        body = resp.read(10000).decode('utf-8', errors='ignore')
        parser = TitleParser()
        parser.feed(body)
        print(u, 'STATUS', code, 'TITLE', parser.title.strip())
    except Exception as e:
        print(u, 'ERROR', repr(e))
        sys.exit(2)

sys.exit(0)
