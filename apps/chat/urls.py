from django.urls import path

from apps.chat.views import (UserGetChatRoomAPIView, LastMessagesAPIView, UserChatRoomListAPIView,
                             ConfigureChatSettingsAPIView, GetChatSettingsAPIView)

app_name = 'chat'
urlpatterns = [
    path('rooms/', UserChatRoomListAPIView.as_view(), name='chat_room_list'),
    path('get-user-room/<int:user_id>/', UserGetChatRoomAPIView.as_view(), name='chat_get_room'),
    path('last-messages/<int:room_id>/', LastMessagesAPIView.as_view(), name='chat_last_messages'),

    path('get-settings/', GetChatSettingsAPIView.as_view(), name='get_chat_settings'),
    path('configure-settings/', ConfigureChatSettingsAPIView.as_view(), name='configure_chat_settings'),
]
