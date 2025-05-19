from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from apps.authentication.models import User
from config.models import BaseModel


class ChatRoom(BaseModel):
    """Represents a chat room between two users"""
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creator_chat_rooms')
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriber_chat_rooms')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'chat_room'
        constraints = [
            models.UniqueConstraint(
                fields=['creator', 'subscriber'],
                name='unique_chat_room'
            )
        ]
        ordering = ['-updated_at']

    def clean(self):
        # Ensure users can't chat with themselves
        if self.creator == self.subscriber:
            raise ValidationError(_('Пользователи не могут чатиться с самим собой.'))

        # Check if subscriber is blocked by creator or vice versa
        if BlockedUser.is_blocked(self.creator, self.subscriber):
            raise ValidationError('Чат не доступен - пользователь заблокирован.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Chat between {self.creator} and {self.subscriber}'


class Message(BaseModel):
    """Represents a message in a chat room"""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'chat_message'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender}: {self.content[:10]}...'


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
            raise ValidationError('Users cannot block themselves.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
