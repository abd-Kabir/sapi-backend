# consumers.py
import base64
import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile

from apps.chat.models import ChatRoom, Message, BlockedUser
from apps.files.utils import upload_file

logger = logging.getLogger()


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
        # if room.creator.is_creator and self.user == room.subscriber:
        #     return UserSubscription.objects.filter(
        #         subscriber=self.user,
        #         creator=room.creator,
        #         is_active=True,
        #         end_date__gt=timezone.now()
        #     ).exists()

        return True

    @database_sync_to_async
    def create_message(self, content=None, file_data=None, file_name=None):
        try:
            room = ChatRoom.objects.get(pk=self.room_id)
            message = Message(room=room, sender=self.user)

            if content:
                message.content = content

            if file_data and file_name:
                data = ContentFile(base64.b64decode(file_data), name=file_name)
                file = upload_file(data)
                message.file = file
            message.save()
            return message
        except Exception as e:
            logger.exception(f"create_message failed: {e.args}")
            raise e

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        message_text = text_data_json.get('message')
        file_data = text_data_json.get('file_data')  # base64 file string
        file_name = text_data_json.get('file_name')  # original filename

        db_message = await self.create_message(
            content=message_text,
            file_data=file_data,
            file_name=file_name
        )

        message = {
            'type': 'chat_message',
            'message': message_text,
            'file_url': db_message.file.path if db_message.file else None,
            'sender_id': self.user.id,
            'created_at': db_message.created_at.isoformat(),
            'message_id': db_message.id
        }
        await self.channel_layer.group_send(
            self.room_group_name,
            message
        )

    async def chat_message(self, event):
        if event['sender_id'] != self.user.id:
            message = await Message.objects.aget(pk=event['message_id'])
            message.is_read = True
            await message.asave()
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'file_path': event['file_url'],
            'sender_id': event['sender_id'],
            'created_at': event['created_at'],
            'message_id': event['message_id']
        }))
