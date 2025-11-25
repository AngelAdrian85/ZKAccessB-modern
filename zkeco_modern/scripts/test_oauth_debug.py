import os
import sys

# Ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
import django
django.setup()

from django.test import Client

def main():
    client = Client()
    resp = client.get('/oauth-debug/', {'code': 'TEST', 'state': 'XYZ'})
    print('STATUS:', resp.status_code)
    print('LENGTH:', len(resp.content))
    print('BODY:\n')
    try:
        print(resp.content.decode('utf-8'))
    except Exception:
        print(resp.content)

if __name__ == '__main__':
    main()
