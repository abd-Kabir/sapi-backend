from django.urls import re_path, path

from apps.chat.consumers import ChatConsumer

websocket_urlpatterns = [
    # re_path(r'ws/chat/(?P<room_id>\w+)/$', ChatConsumer.as_asgi()),
    path('ws/chat/<int:room_id>/', ChatConsumer.as_asgi()),
]
