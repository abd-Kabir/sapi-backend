from celery import shared_task

from apps.authentication.models import User, NotificationDistribution
from apps.authentication.services import send_notification_to_users, resubscribe


@shared_task
def send_notification_task(user_ids, title, text, notif_dist_id):
    users = User.objects.filter(id__in=user_ids)
    send_notification_to_users(users, title, text)
    instance = NotificationDistribution.objects.filter(pk=notif_dist_id)
    if instance.exists():
        instance = instance.first()
        instance.status = 'sent'
        instance.save()


@shared_task
def resubscribe_task():
    users = User.objects.filter(subscriptions__is_active=True).distinct()
    for user in users:
        resubscribe(user)