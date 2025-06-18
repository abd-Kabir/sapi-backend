from rest_framework import serializers

from apps.chat.models import Message, ChatRoom, ChatSettings
from apps.files.serializers import FileSerializer


class UserChatRoomListSerializer(serializers.ModelSerializer):
    chat_with = serializers.SerializerMethodField(read_only=True)
    chat_with_username = serializers.SerializerMethodField(read_only=True)
    last_message = serializers.SerializerMethodField(read_only=True)

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

    def get_last_message(self, room):
        user = self.context['request'].user
        message = room.messages.order_by('-id').first()
        file = FileSerializer(message.file).data
        if message.sender != user:
            is_read = message.is_read
        else:
            is_read = True
        return {'id': message.id, 'content': message.content, 'file': file, 'is_read': is_read}

    class Meta:
        model = ChatRoom
        fields = [
            'id',
            'chat_with',
            'chat_with_username',
            'last_message',
        ]


class MessageListSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.username', read_only=True)
    is_read = serializers.SerializerMethodField()

    def get_is_read(self, obj):
        user = self.context['request'].user
        if obj.sender != user:
            obj.is_read = True
            obj.save()
            return True
        return None

    class Meta:
        model = Message
        fields = [
            'id',
            'content',
            'sender_id',
            'sender',
            'is_read',
            'created_at',
        ]


class ChatSettingsSerializer(serializers.ModelSerializer):
    subscription_plans = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)
    minimum_message_donation = serializers.IntegerField(required=False, write_only=True)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.can_chat == 'subscribers':
            representation['subscription_plans'] = instance.subscription_plans
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
        ]
