#!/usr/bin/env sh
set -e

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Optionally create a superuser when ADMIN_USER/ADMIN_EMAIL/ADMIN_PASS are provided
if [ -n "${ADMIN_USER:-}" ] && [ -n "${ADMIN_PASS:-}" ]; then
  echo "Creating superuser ${ADMIN_USER} if not exists..."
  python - <<PY
from django.contrib.auth import get_user_model
User = get_user_model()
username = '${ADMIN_USER}'
email = '${ADMIN_EMAIL:-admin@example.com}'
password = '${ADMIN_PASS}'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print('Superuser created')
else:
    print('Superuser already exists')
PY
fi

echo "Starting gunicorn..."
exec gunicorn zkeco_config.wsgi:application --bind 0.0.0.0:8000
