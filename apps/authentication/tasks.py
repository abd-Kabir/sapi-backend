from celery import shared_task

from apps.authentication.models import User
from apps.authentication.services import send_notification_to_users


@shared_task
def print_hello():
    print("Hello from Celery!")

@shared_task
def send_notification_task(user_ids, title, text):
    users = User.objects.filter(id__in=user_ids)
    send_notification_to_users(users, title, text)
