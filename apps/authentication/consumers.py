# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone

from apps.authentication.models import ChatRoom, Message, BlockedUser, UserSubscription


class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({"message": "Connected"}))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({"echo": data}))


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.user = self.scope['user']

        if isinstance(self.user, AnonymousUser):
            await self.close()
            return

        # Verify user has access to this chat room
        chat_access_verification = await self.verify_chat_access()
        if not chat_access_verification:
            await self.close()
            return

        self.room_group_name = f'chat_{self.room_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    @database_sync_to_async
    def verify_chat_access(self):
        try:
            room = ChatRoom.objects.get(pk=self.room_id)
        except ChatRoom.DoesNotExist:
            return False

        # Check if current user is part of this chat
        if self.user not in [room.creator, room.subscriber]:
            return False

        # Check if users are blocked
        if BlockedUser.is_blocked(room.creator, room.subscriber):
            return False

        # If chatting with creator, check subscription
        if room.creator.is_creator and self.user == room.subscriber:
            return UserSubscription.objects.filter(
                subscriber=self.user,
                creator=room.creator,
                is_active=True,
                end_date__gt=timezone.now()
            ).exists()

        return True

    @database_sync_to_async
    def create_message(self, content):
        room = ChatRoom.objects.get(pk=self.room_id)
        message = Message.objects.create(
            room=room,
            sender=self.user,
            content=content
        )
        return message

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Save message to database
        db_message = await self.create_message(message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': self.user.id,
                'timestamp': db_message.timestamp.isoformat(),
                'message_id': db_message.id
            }
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp'],
            'message_id': event['message_id']
        }))
