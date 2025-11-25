"""
ASGI config for zkeco_config project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zkeco_config.settings")

import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
 
application = get_asgi_application()
django.setup()

try:
	# Import via fully-qualified app path to avoid root-level shim exclusion
	from zkeco_modern.agent.routing import websocket_urlpatterns as agent_ws
except Exception:
	agent_ws = []

application = ProtocolTypeRouter(
	{
		"http": get_asgi_application(),
		"websocket": AuthMiddlewareStack(URLRouter(agent_ws)),
	}
)
