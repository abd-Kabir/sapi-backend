from django.db.models import Manager


class CardManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
