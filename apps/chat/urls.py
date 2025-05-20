from django.urls import path

from apps.chat.views import UserChatRoomAPIView, LastMessagesAPIView

app_name = 'chat'
urlpatterns = [
    path('get-room/<int:user_id>/', UserChatRoomAPIView.as_view(), name='chat_get_room'),
    path('last-messages/<int:room_id>/', LastMessagesAPIView.as_view(), name='chat_last_messages'),
]
