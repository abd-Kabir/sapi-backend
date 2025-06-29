import calendar
from datetime import date, timedelta

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.authentication.managers import CardManager, UserManager, AllUserManager
from apps.content.models import ReportTypes
from config.models import BaseModel


class CardType(models.TextChoices):
    visa = 'visa', 'VISA'
    uzcard = 'uzcard', 'UZCARD'
    humo = 'humo', 'HUMO'
    mastercard = 'mastercard', 'Mastercard'


class PaymentType(models.TextChoices):
    card = 'card', _('Карта')
    click = 'click', 'Click'
    payme = 'payme', 'Payme'


class ActivityType(models.TextChoices):
    donation = 'donation', _('Задонатил')
    commented = 'commented', _('Оставил комментарий')
    replied = 'replied', _('Оставил ответный комментарий')
    followed = 'followed', _('Фолловнул')
    subscribed = 'subscribed', _('Подписался')
    liked_post = 'liked_post', _('Лайкнул пост')
    liked_comment = 'liked_comment', _('Лайкнул комментарий')


class NotifDisPlatformType(models.TextChoices):
    push_notification = 'push_notification', _('Push-уведомление')


class UserType(models.TextChoices):
    all = 'all', _('Все пользователи')
    creators = 'creators', _('Креаторы')
    users = 'users', _('Обычные пользователи')


class NotifDisStatus(models.TextChoices):
    waiting = 'waiting', _('Ожидается')
    draft = 'draft', _('Драфт')
    sent = 'sent', _('Отправлен')


class PermissionTypes(models.TextChoices):
    VIEW_STATISTICS = 'VIEW_STATISTICS', _('Просмотр статистики')
    MODIFY_STATISTICS = 'MODIFY_STATISTICS', _('Редактирование статистики')

    VIEW_NOTIFICATIONS = 'VIEW_NOTIFICATIONS', _('Просмотр рассылок уведомлений')
    MODIFY_NOTIFICATIONS = 'MODIFY_NOTIFICATIONS', _('Редактирование рассылок уведомлений')

    VIEW_REPORTS = 'VIEW_REPORTS', _('Просмотр жалоб')
    MODIFY_REPORTS = 'MODIFY_REPORTS', _('Редактирование жалоб')

    VIEW_CREATORS = 'VIEW_CREATORS', _('Просмотр креаторов')
    MODIFY_CREATORS = 'MODIFY_CREATORS', _('Редактирование креаторов')

    VIEW_CHATS = 'VIEW_CHATS', _('Просмотр чата поддержки')
    MODIFY_CHATS = 'MODIFY_CHATS', _('Редактирование чата поддержки')

    VIEW_ADMINS = 'VIEW_ADMINS', _('Просмотр администраторов')
    MODIFY_ADMINS = 'MODIFY_ADMINS', _('Редактирование администраторов')

    @staticmethod
    def categories() -> dict:
        """
        return the categories of permissions
        response is a dict type
        value: tuple -> (Name of Category, Has children, Only View)
        """

        return {
            'STATISTICS': 'Статистика',
            'SENDING_NOTIFICATIONS': 'Рассылка уведомлений',
            'REPORTS': 'Жалобы',
            'CREATORS': 'Креаторы',
            'CHATS': 'Чаты',
            'ADMINS': 'Администраторы',
        }


class UserPermissions(models.Model):
    permission = models.CharField(max_length=55, choices=PermissionTypes.choices)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='permissions')

    class Meta:
        db_table = 'user_permission'


class User(AbstractUser):
    email = None
    first_name = models.CharField(_("first name"), max_length=150, blank=True, null=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True, null=True)

    username_validator = UnicodeUsernameValidator()
    temp_username = models.CharField(_("temp username"), max_length=150, blank=True, null=True)
    username = models.CharField(_("username"), max_length=150, unique=True, validators=[username_validator],
                                null=True, blank=True,
                                help_text=_("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."),
                                error_messages={"unique": _("A user with that username already exists.")})
    temp_phone_number = models.CharField(max_length=30, null=True, blank=True)
    phone_number = models.CharField(max_length=30, unique=True, null=True, blank=True)
    is_sms_verified = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_creator = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    is_blocked_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='admin_blocked_users')
    block_reason = models.CharField(choices=ReportTypes.choices, max_length=20, null=True)
    block_desc = models.TextField(null=True, blank=True)

    creator_description = models.TextField(null=True, blank=True)
    multibank_account = models.CharField(max_length=20, null=True, blank=True)
    multibank_verified = models.BooleanField(default=False)
    minimum_message_donation = models.PositiveBigIntegerField(default=0)
    sapi_share = models.PositiveSmallIntegerField(default=10)
    pinfl = models.CharField(null=True, blank=True, max_length=14)

    profile_photo = models.OneToOneField('files.File', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='profile_photo')
    profile_banner_photo = models.OneToOneField('files.File', on_delete=models.SET_NULL, null=True, blank=True,
                                                related_name='profile_banner_photo')
    category = models.ForeignKey('content.Category', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='users')

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = UserManager()
    all_objects = AllUserManager()

    def subscribers_count(self):
        """Return the number of subscribers this user has"""
        return self.subscribers.count()

    def has_subscription(self, subscriber):
        return self.subscribers.filter(subscriber=subscriber).exists()

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

    def is_blocked_by_user(self, user):
        """Check if this user is blocked another user"""
        return self.blocked_by.filter(blocker=user).exists()

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

    def toggle_block(self, user_to_block):
        """
        Toggle block/unblock another user
        Returns tuple: (action_taken, block_relation)
        where action_taken is either 'blocked' or 'unblocked'
        """
        if self == user_to_block:
            raise ValueError("You cannot block yourself.")

        block_relation = BlockedUser.objects.filter(
            blocker=self,
            blocked=user_to_block
        ).first()

        if block_relation:
            block_relation.delete()
            return 'unblocked', None
        else:
            new_relation = BlockedUser.objects.create(
                blocker=self,
                blocked=user_to_block
            )
            return 'blocked', new_relation

    class Meta:
        db_table = 'user'


class Card(BaseModel):
    is_active = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_main = models.BooleanField(default=False)
    card_owner = models.CharField(max_length=155, null=True)
    number = models.CharField(max_length=16)
    token = models.TextField(null=True, blank=True)
    expiration = models.CharField(max_length=5)
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
        self.is_active = False
        self.token = None
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


class UserSubscription(BaseModel):
    """Active subscriptions of users to creators"""
    subscriber_card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='subscriptions')
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscribers')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    commission_by_subscriber = models.BooleanField(default=False)
    payment_type = models.CharField(choices=PaymentType.choices, default=PaymentType.card, null=True, blank=True)
    payment_reference = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'user_subscription'
        constraints = [
            models.UniqueConstraint(fields=['subscriber', 'creator', 'plan'],
                                    name='user_subs_unique_subscriber_creator_plan')
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


class BlockedUser(BaseModel):
    """Represents a user blocking another user"""
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_users')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')

    class Meta:
        db_table = 'blocked_user'
        constraints = [
            models.UniqueConstraint(
                fields=['blocker', 'blocked'],
                name='unique_block'
            )
        ]

    @classmethod
    def is_blocked(cls, user1, user2):
        """Check if either user has blocked the other"""
        return cls.objects.filter(
            models.Q(blocker=user1, blocked=user2) |
            models.Q(blocker=user2, blocked=user1)
        ).exists()

    def clean(self):
        if self.blocker == self.blocked:
            raise ValidationError(_('Пользователь не может заблокировать себя.'))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.blocker} blocked {self.blocked}"


class Fundraising(BaseModel):
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    current_amount = models.PositiveBigIntegerField(default=0)
    goal = models.PositiveBigIntegerField()

    minimum_donation = models.PositiveBigIntegerField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fundraising')

    class Meta:
        db_table = 'fundraising'


class Donation(BaseModel):
    amount = models.PositiveBigIntegerField()
    message = models.TextField(null=True, blank=True)
    card = models.ForeignKey(Card, on_delete=models.SET_NULL, null=True, related_name='donations')
    fundraising = models.ForeignKey(Fundraising, on_delete=models.SET_NULL, null=True, related_name='donations')

    donator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='donations_made')
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='donations_received')

    def __str__(self):
        return f"Donation of {self.amount} by {self.donator} to {self.creator}"

    def clean(self):
        if self.donator == self.creator:
            raise ValidationError(_('Вы не можете донатить самому себе.'))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'donation'
        indexes = [
            models.Index(fields=['donator']),
            models.Index(fields=['creator']),
        ]


class UserActivity(BaseModel):
    type = models.CharField(choices=ActivityType.choices, max_length=20)
    content = models.TextField(null=True, blank=True)
    content_id = models.CharField(max_length=50, null=True, blank=True)
    initiator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_initiator', null=True)
    content_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_owner', null=True)

    class Meta:
        db_table = 'user_activity'


class NotificationDistribution(BaseModel):
    is_draft = models.BooleanField(default=False)
    title_uz = models.CharField(max_length=155, null=True, blank=True)
    title_ru = models.CharField(max_length=155, null=True, blank=True)
    text_uz = models.TextField(null=True, blank=True)
    text_ru = models.TextField(null=True, blank=True)
    sending_date = models.DateTimeField(null=True, blank=True)

    status = models.CharField(choices=NotifDisStatus.choices, default=NotifDisStatus.waiting, max_length=55)
    user_type = models.CharField(choices=UserType.choices, default=UserType.all, max_length=55)
    # type = models.CharField(choices=NotifDisPlatformType.choices, default=NotifDisPlatformType.push_notification, max_length=55)
    types = ArrayField(models.CharField(max_length=55, choices=NotifDisPlatformType.choices), default=list)

    class Meta:
        db_table = 'notification_distribution'
