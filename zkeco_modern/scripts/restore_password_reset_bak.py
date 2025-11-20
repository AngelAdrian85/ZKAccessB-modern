from pathlib import Path

p = Path('..') / 'zkeco' / 'units' / 'adms' / 'mysite' / 'templates' / 'registration' / 'password_reset_email.html'
bak = p.with_suffix(p.suffix + '.bak')

print('file', p)
print('bak', bak)
if bak.exists():
    p.write_text(bak.read_text(encoding='utf-8'), encoding='utf-8')
    print('Restored from .bak')
else:
    print('.bak not found')
from pathlib import Path
p = Path('..')/ 'zkeco' / 'units' / 'adms' / 'mysite' / 'templates' / 'registration' / 'password_reset_email.html'
bak = p.with_suffix(p.suffix + '.bak')
print('file', p)
print('bak', bak)
if bak.exists():
    p.write_text(bak.read_text(encoding='utf-8'), encoding='utf-8')
    print('Restored from .bak')
else:
    print('.bak not found')
