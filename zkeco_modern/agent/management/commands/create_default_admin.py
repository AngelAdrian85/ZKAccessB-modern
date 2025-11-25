from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create a default superuser 'admin' if it does not exist. Password: admin123"

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.filter(username='admin').exists():
            self.stdout.write('admin user already exists')
        else:
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write('created admin:admin123')
