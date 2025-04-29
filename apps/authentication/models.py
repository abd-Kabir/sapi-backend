from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from config.models import BaseModel


class CardType(models.TextChoices):
    visa = 'visa', 'VISA'
    uzcard = 'uzcard', 'UZCARD'
    humo = 'humo', 'HUMO'
    mastercard = 'mastercard', 'Mastercard'


class User(AbstractUser):
    email = None
    first_name = None
    last_name = None

    username_validator = UnicodeUsernameValidator()
    username = models.CharField(_("username"), max_length=150, unique=True, validators=[username_validator],
                                null=True, blank=True,
                                help_text=_("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."),
                                error_messages={"unique": _("A user with that username already exists.")})
    phone_number = models.CharField(max_length=30, unique=True)
    is_sms_verified = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_creator = models.BooleanField(default=False)

    creator_description = models.TextField(null=True, blank=True)
    multibank_account = models.CharField(max_length=20, null=True, blank=True)
    multibank_verified = models.BooleanField(default=False)

    profile_photo = models.OneToOneField('files.File', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='profile_photo')
    profile_banner_photo = models.OneToOneField('files.File', on_delete=models.SET_NULL, null=True, blank=True,
                                                related_name='profile_banner_photo')
    category = models.ForeignKey('content.Category', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='users')

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'user'


class Card(BaseModel):
    is_deleted = models.BooleanField(default=False)
    is_main = models.BooleanField(default=False)
    card_owner = models.CharField(max_length=155)
    number = models.CharField(max_length=16)
    expiration = models.CharField(max_length=4)
    type = models.CharField(max_length=10, choices=CardType.choices, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards', null=True)

    class Meta:
        db_table = 'card'


class Subscription(BaseModel):
    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    name = models.CharField(max_length=55)
    description = models.TextField(null=True, blank=True)
    price = models.PositiveBigIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    banner = models.ForeignKey('files.File', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='subscriptions')

    # def subscribers_count(self):
    #     return self.user

    class Meta:
        db_table = 'subscription'
