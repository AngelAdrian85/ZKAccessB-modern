"""
WSGI config for zkeco_config project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zkeco_config.settings")

application = get_wsgi_application()
