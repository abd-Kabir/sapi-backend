import re
import random

from django.utils.timezone import timedelta, now
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from apps.integrations.api_integrations.sms import sms_app
from apps.integrations.models import SMSConfirmation, sms_message_purpose_tool
from config.core.api_exceptions import APIValidation


def only_phone_numbers(phone):
    """
    return: Remove all non-digit characters and return phone-number
    """
    phone_number = re.sub(r'\D', '', phone)
    if not phone_number:
        raise APIValidation(_('Введите номер телефона'), status_code=status.HTTP_400_BAD_REQUEST)
    return phone_number


def generate_sms_code() -> str:
    # return '111111'
    return str(random.randint(100000, 999999))


def can_request_sms(user, purpose):
    last_request = SMSConfirmation.objects.filter(user=user, purpose=purpose).order_by('-requested_at').first()
    if last_request and last_request.requested_at > now() - timedelta(minutes=1):  # 1-minute cooldown
        raise APIValidation(_('Пожалуйста, подождите минуту, прежде чем запросить еще один код.'), status_code=400)
    return True


def send_sms(phone_number: str, purpose, code: str = generate_sms_code()):
    message = sms_message_purpose_tool(purpose, code)
    phone_number = only_phone_numbers(phone_number)
    return sms_app.send_sms(data={
        'mobile_phone': phone_number,
        'message': message,
        'from': '4546'
    })


def sms_confirmation_open(user, purpose):
    can_request_sms(user, purpose)

    code = generate_sms_code()
    expires_at = now() + timedelta(minutes=10)
    SMSConfirmation.objects.update_or_create(
        user=user,
        purpose=purpose,
        is_used=False,
        defaults={'code': code, 'expires_at': expires_at, 'requested_at': now(),
                  'phone_number': only_phone_numbers(user.phone_number)}
    )
    send_sms(user.phone_number, purpose, code)
    return True


def sms_confirmation_open_phone_number(phone_number, purpose):
    phone_number = only_phone_numbers(phone_number)

    code = generate_sms_code()
    expires_at = now() + timedelta(minutes=10)
    SMSConfirmation.objects.update_or_create(
        phone_number=phone_number,
        purpose=purpose,
        is_used=False,
        defaults={'code': code, 'expires_at': expires_at, 'requested_at': now()}
    )
    send_sms(phone_number, purpose, code)
    return True


def verify_sms_code(user, code):
    sms_confirmation = SMSConfirmation.objects.filter(code=code, user=user, is_used=False).first()
    if not sms_confirmation or sms_confirmation.is_expired():
        raise APIValidation(_('Недействительный или просроченный код.'), status_code=status.HTTP_400_BAD_REQUEST)
    sms_confirmation.is_used = True
    sms_confirmation.save()
    return True


def verify_sms_code_phone_number(phone_number, code):
    phone_number = only_phone_numbers(phone_number)

    sms_confirmation = SMSConfirmation.objects.filter(code=code,
                                                      phone_number=phone_number,
                                                      is_used=False).first()
    if not sms_confirmation or sms_confirmation.is_expired():
        raise APIValidation(_('Недействительный или просроченный код.'), status_code=status.HTTP_400_BAD_REQUEST)
    sms_confirmation.is_used = True
    sms_confirmation.save()
    return True
