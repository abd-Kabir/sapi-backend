# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.utils import timezone

from apps.authentication.models import UserSubscription
from apps.chat.models import ChatRoom, Message, BlockedUser


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.user = self.scope['user']

        if isinstance(self.user, AnonymousUser):
            await self.close()
            return

        # Verify user has access to this chat room
        chat_access_verification = await self.verify_chat_access()
        if not chat_access_verification:
            await self.close()
            return

        self.room_group_name = f'chat_{self.user_id}'

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
        if int(self.user_id) == self.user.id:
            return False

        room = self.get_room()

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

    def get_room(self):
        room = (
            ChatRoom.objects
            .filter(
                (Q(creator=self.user) | Q(creator_id=self.user_id)) &
                (Q(subscriber=self.user) | Q(subscriber_id=self.user_id))
            )
            .first()
        )
        if not room:
            return ChatRoom.objects.create(creator_id=self.user_id, subscriber=self.user)
        return room

        # if ChatRoom.objects.filter(creator_id=self.user_id, subscriber=self.user).exists():
        #     return ChatRoom.objects.filter(creator_id=self.user_id, subscriber=self.user).first()
        # elif ChatRoom.objects.filter(creator_id=self.user.id, subscriber_id=self.user_id).exists():
        #     return ChatRoom.objects.filter(creator_id=self.user.id, subscriber_id=self.user_id).first()
        # else:

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
