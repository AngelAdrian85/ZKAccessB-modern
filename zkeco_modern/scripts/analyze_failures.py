import json, collections, os
p = os.path.join(os.path.dirname(__file__), 'failures.json')
if not os.path.exists(p):
    print('failures.json not found', p)
    raise SystemExit(1)
with open(p, encoding='utf8') as fh:
    failures = json.load(fh)
counts = collections.Counter([f['error'] for f in failures])
print('Top error patterns:')
for err, c in counts.most_common():
    print(f'{c:4d}  {err}')
print('\nSample files per top errors:\n')
for err, c in counts.most_common()[:8]:
    print('---', err)
    for f in failures:
        if f['error'] == err:
            print(' ', f['file'])
            break
