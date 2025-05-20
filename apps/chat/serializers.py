from rest_framework import serializers

from apps.chat.models import Message


class MessageListSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.username', read_only=True)
    is_read = serializers.SerializerMethodField()

    def get_is_read(self, obj):
        user = self.context['request'].user
        if obj.sender != user:
            return obj.is_read
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
