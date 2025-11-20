import importlib.util, os
os.environ['INCLUDE_LEGACY']='1'
from pathlib import Path
spec = importlib.util.find_spec('mysite')
print('spec:', spec)
if spec:
    print('origin:', spec.origin)
    print('loader:', spec.loader)
    try:
        if spec.origin and Path(spec.origin).exists():
            b = Path(spec.origin).read_bytes()[:16]
            print('first bytes:', b)
    except Exception as e:
        print('read error:', e)
