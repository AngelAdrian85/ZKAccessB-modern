from django.urls import path, re_path
from . import consumers

websocket_urlpatterns = [
    path("ws/monitor/", consumers.MonitorConsumer.as_asgi()),
    path("ws/events/", consumers.EventsConsumer.as_asgi()),
    path("ws/access-levels/", consumers.AccessLevelsConsumer.as_asgi()),
]
