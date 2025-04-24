from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone_number = models.CharField(max_length=30, unique=True)

    class Meta:
        db_table = 'User'
