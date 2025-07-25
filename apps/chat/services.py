from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from apps.authentication.models import Donation, UserSubscription
from config.core.api_exceptions import APIValidation


def check_chatting_verification(user, another_user):
    another_user_configs = another_user.chat_settings.all()

    if not another_user_configs.filter(can_chat='everyone').exists():
        if not another_user_configs.filter(can_chat='nobody').exists():
            if another_user_configs.filter(can_chat='subscribers').exists():
                is_subscribed = UserSubscription.objects.filter(
                    subscriber=user,
                    creator=another_user,
                    end_date__gt=timezone.now()
                ).exists()

                if not is_subscribed:
                    raise APIValidation(_('Могут общаться только пользователи с подпиской этого креатора'),
                                        status_code=status.HTTP_403_FORBIDDEN)
            if another_user_configs.filter(can_chat='donations').exists():
                donation_settings = another_user_configs.filter(can_chat='donations').first()
                if donation_settings.minimum_message_donation <= 0:
                    raise APIValidation(
                        _(f'Могут общаться только пользователи которые задонатили этому креатору минимум {donation_settings.minimum_message_donation}'),
                        status_code=status.HTTP_403_FORBIDDEN
                    )
                total_donation = Donation.objects.filter(
                    donator=user,
                    creator=another_user,
                ).aggregate(total=Sum('amount'))['total']
                if total_donation < donation_settings.minimum_message_donation:
                    raise APIValidation(
                        _(f'Могут общаться только пользователи которые задонатили этому креатору минимум {donation_settings.minimum_message_donation}'),
                        status_code=status.HTTP_403_FORBIDDEN
                    )
            return True
        else:
            raise APIValidation(_('Этот пользователь закрыл чат'), status_code=status.HTTP_403_FORBIDDEN)
    else:
        return True
