from __future__ import absolute_import, unicode_literals
import os
from datetime import timedelta

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

app.config_from_object('django.conf:settings', namespace='CELERY')

# app.conf.update(
#     task_time_limit=600,
#     task_soft_time_limit=550,
# )

app.autodiscover_tasks()

# Schedule your task here
app.conf.beat_schedule = {
    # 'run-cron-crop-contracts': {
    #     'task': 'apps.integrations.tasks.cron_crop_contracts',
    #     'schedule': crontab(minute='*/5'),
    # },
    # 'run-cron-test-task': {
    #     'task': 'apps.authentication.tasks.print_hello',
    #     # 'schedule': crontab(minute='*/5'),
    #     'schedule': timedelta(seconds=30),
    # },
    'run-cron-resubscribe-task': {
        'task': 'apps.authentication.tasks.resubscribe_task',
        'schedule': crontab(minute=0, hour='0,12'),
    },
}
