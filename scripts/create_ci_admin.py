import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
import django
django.setup()
from django.contrib.auth import get_user_model  # noqa: E402 (django.setup() must run before importing Django models)
User = get_user_model()
username = 'ci_admin'
email = 'admin@example.com'
password = 'AdminPass123'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print('Created superuser', username)
else:
    print('Superuser already exists')
