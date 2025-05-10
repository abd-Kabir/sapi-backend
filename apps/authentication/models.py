import calendar
from datetime import date, timedelta

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.authentication.managers import CardManager
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

    def followers_count(self):
        """Return the number of followers this user has"""
        return self.followers.count()

    def following_count(self):
        """Return the number of users this user is following"""
        return self.following.count()

    def is_following(self, user):
        """Check if this user is following another user"""
        return self.following.filter(followed=user).exists()

    def is_followed_by(self, user):
        """Check if this user is followed by another user"""
        return self.followers.filter(follower=user).exists()

    def toggle_follow(self, user_to_follow):
        """
        Toggle follow/unfollow another user
        Returns tuple: (action_taken, follow_relation)
        where action_taken is either 'followed' or 'unfollowed'
        """
        if self == user_to_follow:
            raise ValueError("You cannot follow yourself.")

        follow_relation = UserFollow.objects.filter(
            follower=self,
            followed=user_to_follow
        ).first()

        if follow_relation:
            follow_relation.delete()
            return 'unfollowed', None
        else:
            new_relation = UserFollow.objects.create(
                follower=self,
                followed=user_to_follow
            )
            return 'followed', new_relation

    class Meta:
        db_table = 'user'


class Card(BaseModel):
    is_deleted = models.BooleanField(default=False)
    is_main = models.BooleanField(default=False)
    card_owner = models.CharField(max_length=155)
    number = models.CharField(max_length=16)
    expiration = models.CharField(max_length=4)
    cvc_cvv = models.CharField(max_length=5, null=True, blank=True)
    type = models.CharField(max_length=10, choices=CardType.choices, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards', null=True)

    objects = CardManager()
    all_objects = models.Manager()

    @property
    def card_pan(self):
        return f'*{self.number[-4:]}' if self.number else None

    def delete_card(self):
        if self.is_main:
            self.is_main = False
            another_card = Card.objects.exclude(pk=self.pk).first()
            if another_card:
                another_card.is_main = True
                another_card.save()
        self.is_deleted = True
        self.save()

    def set_main(self, is_main):
        if is_main:
            Card.objects.exclude(id=self.id).update(is_main=False)
            self.is_main = True
            self.save()
            return True
        return False

    class Meta:
        db_table = 'card'


class SubscriptionPlan(BaseModel):
    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=55)
    description = models.TextField(null=True, blank=True)
    price = models.PositiveBigIntegerField()
    duration = models.DurationField(null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscription_plans')
    banner = models.ForeignKey('files.File', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='subscription_plans')

    # def subscribers_count(self):
    #     return self.user

    def set_duration(self):
        today = date.today()
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        self.duration = timedelta(days=days_in_month)
        self.save()

    class Meta:
        db_table = 'subscription_plan'


class UserSubscription(models.Model):
    """Active subscriptions of users to creators"""
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscribers')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    payment_reference = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'user_subscription'
        constraints = [
            models.UniqueConstraint(fields=['subscriber', 'creator'], name='user_subs_unique_subscriber_creator')
        ]

    def save(self, *args, **kwargs):
        if not self.end_date and self.plan:
            self.end_date = timezone.now() + self.plan.duration
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subscriber} -> {self.creator} ({self.plan})"


class UserFollow(models.Model):
    """Free following relationship between users"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')  # follower
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')  # *creator
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_follow'
        constraints = [
            models.UniqueConstraint(fields=['follower', 'followed'], name='followers_unique_followed_follower')
        ]
        indexes = [
            models.Index(fields=['follower']), models.Index(fields=['followed']),
        ]

    def __str__(self):
        return f"{self.follower} follows {self.followed}"
