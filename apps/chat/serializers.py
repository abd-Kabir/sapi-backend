from rest_framework import serializers

from apps.authentication.models import SubscriptionPlan, BlockedUser
from apps.chat.models import Message, ChatRoom, ChatSettings
from apps.files.serializers import FileSerializer


class UserChatRoomListSerializer(serializers.ModelSerializer):
    profile_photo = serializers.SerializerMethodField(read_only=True)
    chat_with = serializers.SerializerMethodField(read_only=True)
    chat_with_username = serializers.SerializerMethodField(read_only=True)
    new_messages_count = serializers.SerializerMethodField(read_only=True)
    last_message = serializers.SerializerMethodField(read_only=True)

    def get_profile_photo(self, room):
        user = self.context['request'].user
        if room.subscriber == user:
            chat_with = room.creator
        else:
            chat_with = room.subscriber
        profile_photo = FileSerializer(chat_with.profile_photo).data if chat_with.profile_photo else None
        return profile_photo

    def get_chat_with(self, room):
        user = self.context['request'].user
        if room.subscriber == user:
            chat_with = room.creator
        else:
            chat_with = room.subscriber
        return chat_with.id

    def get_chat_with_username(self, room):
        user = self.context['request'].user
        if room.subscriber == user:
            chat_with = room.creator
        else:
            chat_with = room.subscriber
        return chat_with.username

    def get_new_messages_count(self, room):
        user = self.context['request'].user
        messages_count = room.messages.filter(is_read=False).exclude(sender=user).count()
        return messages_count

    def get_last_message(self, room):
        user = self.context['request'].user
        message = room.messages.order_by('-id').first()
        file = None
        is_read = None
        message_id = None
        content = None
        created_at = None
        if message:
            message_id = message.id
            content = message.content
            created_at = message.created_at

            file = FileSerializer(message.file).data if message.file else None
            if message.sender != user:
                is_read = message.is_read
            else:
                is_read = True
        return {'id': message_id, 'content': content, 'file': file, 'is_read': is_read, 'created_at': created_at}

    class Meta:
        model = ChatRoom
        fields = [
            'id',
            'profile_photo',
            'chat_with',
            'chat_with_username',
            'new_messages_count',
            'last_message',
        ]


class MessageListSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.username', read_only=True)
    is_read = serializers.SerializerMethodField()
    # is_blocked = serializers.SerializerMethodField()
    # is_blocked_by_me = serializers.SerializerMethodField()
    type_display = serializers.CharField(source='get_type_display', read_only=True, allow_null=True)
    file = FileSerializer(read_only=True, allow_null=True)

    def get_is_read(self, obj):
        user = self.context['request'].user
        if obj.sender != user:
            obj.is_read = True
            obj.save()
            return True
        return obj.is_read

    # def get_is_blocked(self, obj):
    #     user = self.context['request'].user
    #     return BlockedUser.blocked_by(user, obj.sender)
    #
    # def get_is_blocked_by_me(self, obj):
    #     user = self.context['request'].user
    #     return BlockedUser.blocked_by(obj.sender, user)

    class Meta:
        model = Message
        fields = [
            'id',
            'type',
            'type_display',
            'file',
            'content',
            'sender_id',
            'sender',
            'is_read',
            'created_at',
            # 'is_blocked',
            # 'is_blocked_by_me'
        ]


class ChatSettingsSerializer(serializers.ModelSerializer):
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())
    subscription_plans = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)
    minimum_message_donation = serializers.IntegerField(required=False, write_only=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.can_chat == 'subscribers':
            subscription_plans_ids = instance.subscription_plans
            subscription_plans = []
            for plan in subscription_plans_ids:
                plan_instance = SubscriptionPlan.objects.get(pk=plan)
                subscription_plans.append({
                    'id': plan_instance.id,
                    'name': plan_instance.name
                })
            representation['subscription_plans'] = subscription_plans
        elif instance.can_chat == 'donations':
            representation['minimum_message_donation'] = instance.minimum_message_donation
        return representation

    class Meta:
        model = ChatSettings
        fields = [
            'id',
            'can_chat',
            'subscription_plans',
            'minimum_message_donation',
            'creator',
        ]
