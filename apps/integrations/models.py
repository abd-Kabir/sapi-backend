import uuid

from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import User
from config.models import BaseModel

sms_message_purpose = {
    'register': 'Ваш код для регистрации на платформе Sapi.uz: {code}',
    'login': 'Ваш код для авторизации на платформе Sapi.uz: {code}',
    'forgot_password': 'Ваш код для восстановления пароля на sapi.uz: {code}',
    'password_reset': 'Ваш код для изменения пароля на sapi.uz: {code}',
    'phone_update': 'Ваш код для изменения номера телефона на sapi.uz: {code}',
    'delete_account': 'Ваш код для удаления аккаунта на платформе Sapi.uz: {code}',
}


def sms_message_purpose_tool(purpose, code):
    return sms_message_purpose[purpose].format(code=code)


class PurposeEnum(models.TextChoices):
    register = 'register', _("Регистрация")
    login = 'login', _("Авторизация")
    forgot_password = 'forgot_password', _("Забыли пароль")
    password_reset = 'password_reset', _("Сброс пароля")
    phone_update = 'phone_update', _("Обновление телефона")
    delete_account = 'delete_account', _("Удаление аккаунта")


class MultibankTransactionTypeEnum(models.TextChoices):
    donation = 'donation', _("Донат")
    fundraising = 'fundraising', _("Сбор средств")
    subscription = 'subscription', _("Подписка")


class MultibankTransactionStatusEnum(models.TextChoices):
    new = 'new', _("Новый")
    paid = 'paid', _("Оплачено")
    failed = 'failed', _("Провалено")


class SMSConfirmation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sms_confirmations", null=True, blank=True)
    phone_number = models.CharField(max_length=30, null=True, blank=True)
    code = models.CharField(max_length=6)
    purpose = models.CharField(
        max_length=20,
        choices=PurposeEnum.choices,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return now() > self.expires_at

    class Meta:
        db_table = "sms_confirmation"


class MultibankAuthToken(models.Model):
    token = models.TextField()
    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "multibank_auth_token"


class MultibankTransaction(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(choices=MultibankTransactionStatusEnum.choices,
                              default=MultibankTransactionStatusEnum.new, max_length=10, null=True)
    amount = models.BigIntegerField(null=True)
    sapi_amount = models.BigIntegerField(null=True)
    creator_amount = models.BigIntegerField(null=True)

    store_id = models.SmallIntegerField(null=True)
    transaction_type = models.CharField(choices=MultibankTransactionTypeEnum.choices, max_length=15, null=True)
    transaction_id = models.CharField(max_length=55, null=True)
    card_token = models.TextField(null=True)

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='user_multibank_transactions')
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                related_name='creator_multibank_transactions')

    class Meta:
        db_table = "multibank_transaction"
