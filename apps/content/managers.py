import logging

from django.db.models import Q, Manager
from django.utils.timezone import now

logger = logging.getLogger(__name__)


class PostManager(Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        logger.debug(f'now: {now()}')
        [logger.debug(f'Publication_time of id:{i.id}-- {i.publication_time};') for i in queryset]
        return queryset.filter(
            (Q(publication_time__lte=now()) | Q(publication_time=None)),
            is_posted=True, is_deleted=False, is_blocked=False, user__is_blocked_by__isnull=True
        )
