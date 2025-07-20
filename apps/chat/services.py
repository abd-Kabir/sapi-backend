from django.db.models import Sum
from django.utils import timezone

from apps.authentication.models import Donation, UserSubscription


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
                    return False
            if another_user_configs.filter(can_chat='donations').exists():
                donation_settings = another_user_configs.filter(can_chat='donations').first()
                if donation_settings.minimum_message_donation <= 0:
                    return False
                total_donation = Donation.objects.filter(
                    donator=user,
                    creator=another_user,
                ).aggregate(total=Sum('amount'))['total']
                if total_donation < donation_settings.minimum_message_donation:
                    return False
            return True
        else:
            return False
    else:
        return True
