#!/usr/bin/env python
"""Check and recreate admin user if needed."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zkeco_config.settings')
django.setup()

from django.contrib.auth.models import User

print("[CHECK] Checking existing users...")
users = User.objects.all()
if users.exists():
    for u in users:
        print(f"  - {u.username} (is_staff={u.is_staff}, is_superuser={u.is_superuser})")
else:
    print("  (no users found)")

print("\n[CHECK] Creating/updating admin user...")
admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'is_staff': True,
        'is_superuser': True,
        'email': 'admin@localhost'
    }
)
admin_user.set_password('adminpass')
admin_user.is_staff = True
admin_user.is_superuser = True
admin_user.save()

if created:
    print(f"[CHECK] Created new admin user: admin/adminpass")
else:
    print(f"[CHECK] Updated existing admin user: admin/adminpass")

print("\n[CHECK] Verifying user...")
admin_check = User.objects.get(username='admin')
print(f"  - admin (is_staff={admin_check.is_staff}, is_superuser={admin_check.is_superuser})")
print("\n[SUCCESS] Admin user ready!")
