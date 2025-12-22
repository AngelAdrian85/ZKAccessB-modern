import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()
from agent.models import AccessLevel
levels = AccessLevel.objects.all()
if not levels:
    print('Nu există niciun nivel de acces în baza de date.')
else:
    for lvl in levels:
        print(f'{lvl.name} - {lvl.doors.count()} uși')