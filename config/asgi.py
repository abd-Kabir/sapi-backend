import os
import django
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from apps.chat.middleware import JWTAuthMiddleware
from apps.chat.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django.setup()
application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': JWTAuthMiddleware(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
