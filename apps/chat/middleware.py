# chat/middleware.py
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from channels.db import database_sync_to_async

User = get_user_model()
jwt_authentication = JWTAuthentication()


@database_sync_to_async
def get_user_from_token(token):
    try:
        validated_token = jwt_authentication.get_validated_token(token)
        user = jwt_authentication.get_user(validated_token)
        return user
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Extract token from headers
        headers = dict(scope.get('headers', []))

        if b'authorization' in headers:
            try:
                auth_header = headers[b'authorization'].decode('utf-8')
                token = auth_header.split(' ')[1]  # Get the part after "Bearer "
                scope['user'] = await get_user_from_token(token)
            except (IndexError, AttributeError):
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()

        return await self.app(scope, receive, send)
