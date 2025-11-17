import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
import django

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
    print('Created admin user')
else:
    print('Admin already exists')
