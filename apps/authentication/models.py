from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = None
    first_name = None
    last_name = None

    phone_number = models.CharField(max_length=30, unique=True)
    is_sms_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'user'
