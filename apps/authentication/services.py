from datetime import timedelta

from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import UserActivity, User
from config.core.api_exceptions import APIValidation


def create_activity(activity_type: str, content: str, content_id: str | int, initiator, content_owner):
    """
    types: donation, commented, followed, subscribed, liked
    """
    UserActivity.objects.create(
        type=activity_type,
        content=content,
        content_id=content_id,
        initiator=initiator,
        content_owner=content_owner,
    )


def get_last_week_days():
    today = now().date()
    return [(today - timedelta(days=i)) for i in reversed(range(7))]


def get_last_month_intervals():
    today = now().date()
    return [(today - timedelta(days=30)) + timedelta(days=i * 5) for i in range(7)]

def authenticate_user(request):
    username = request.data.get('username')
    password = request.data.get('password')

    try:
        user = User.objects.get(username=username)
        if user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
    except User.DoesNotExist:
        pass

    raise APIValidation(_('Неправильный логин или пароль'), status_code=403)