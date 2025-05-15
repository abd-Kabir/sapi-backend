from django.urls import re_path

from apps.authentication.consumers import ChatConsumer, TestConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_id>\w+)/$', ChatConsumer.as_asgi()),
    re_path(r'ws/test/$', TestConsumer.as_asgi()),
]
