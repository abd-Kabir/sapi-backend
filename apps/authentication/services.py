from datetime import timedelta

from django.utils.timezone import now

from apps.authentication.models import UserActivity


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
