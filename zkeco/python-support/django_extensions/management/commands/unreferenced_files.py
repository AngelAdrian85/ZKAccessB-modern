from collections import defaultdict
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import models
from django.apps import apps


class Command(BaseCommand):
    help = "Prints a list of all files in MEDIA_ROOT that are not referenced in the database."

    def handle(self, *args, **options):

        if settings.MEDIA_ROOT == '':
            self.stdout.write("MEDIA_ROOT is not set, nothing to do")
            return

        # Get a list of all files under MEDIA_ROOT
        media = []
        for root, dirs, files in os.walk(settings.MEDIA_ROOT):
            for f in files:
                media.append(os.path.abspath(os.path.join(root, f)))

        # Get list of all fields (value) for each model (key)
        # that is a FileField or subclass of a FileField
        model_dict = defaultdict(list)
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                for field in model._meta.fields:
                    if issubclass(field.__class__, models.FileField):
                        model_dict[model].append(field)

        # Get a list of all files referenced in the database
        referenced = []
        for model in model_dict:
            queryset = model.objects.all().iterator()
            for obj in queryset:
                for field in model_dict[model]:
                    try:
                        referenced.append(os.path.abspath(getattr(obj, field.name).path))
                    except Exception:
                        # skip missing/empty file fields
                        continue

        # Print each file in MEDIA_ROOT that is not referenced in the database
        for m in media:
            if m not in referenced:
                self.stdout.write(m)
