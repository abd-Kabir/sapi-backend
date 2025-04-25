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

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'user'


class Card(BaseModel):
    number = models.CharField(max_length=16)
    type = models.CharField(max_length=10)
    class Meta:
        db_table = 'card'
