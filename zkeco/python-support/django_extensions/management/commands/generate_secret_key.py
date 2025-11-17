from random import choice
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generates a new SECRET_KEY that can be used in a project settings file."

    requires_model_validation = False

    def handle(self, *args, **options):
        key = "".join(
            choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)
        )
        self.stdout.write(key)
