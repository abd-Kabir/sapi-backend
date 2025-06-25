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


def permissions_by_category(permissions):
    categories = set({'_'.join(i.split('_')[1:]) for i in permissions})
    categories = {i: [] for i in categories}
    for permission in permissions:
        category_part = '_'.join(permission.split('_')[1:])
        categories[category_part].append(permission)
    return categories


def authenticate_user(request):
    phone_number = request.data.get('phone_number')
    password = request.data.get('password')

    try:
        user = User.objects.get(phone_number=phone_number)
        if user.check_password(password) and user.is_admin:
            refresh = RefreshToken.for_user(user)
            permissions = list(user.permissions.values_list('permission', flat=True))
            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'permissions': permissions,
                'permissions_by_category': permissions_by_category(permissions),
            }
    except User.DoesNotExist:
        pass

    raise APIValidation(_('Неправильный логин или пароль'), status_code=403)
