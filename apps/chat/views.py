from django.db.models import Q
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import User, BlockedUser
from apps.chat.models import ChatRoom, Message
from apps.chat.serializers import MessageListSerializer
from config.core.api_exceptions import APIValidation
from config.core.pagination import APILimitOffsetPagination


class UserChatRoomAPIView(APIView):
    @staticmethod
    def get_user(user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise APIValidation(_('Пользователь не найден'), status_code=status.HTTP_404_NOT_FOUND)

    def get(self, request, user_id, *args, **kwargs):
        chat_started_user = request.user
        writing_to = self.get_user(user_id)

        if BlockedUser.is_blocked(writing_to, chat_started_user):
            raise APIValidation(_('Вы заблокированы этим пользователем'), status_code=status.HTTP_403_FORBIDDEN)

        if chat_started_user.id == writing_to.id:
            raise APIValidation(_('Чат не может быть создан с самим собой'), status_code=status.HTTP_400_BAD_REQUEST)

        room = ChatRoom.objects.filter(
            Q(creator=chat_started_user, subscriber=writing_to) |
            Q(creator=writing_to, subscriber=chat_started_user)
        ).first()

        if not room:
            room = ChatRoom.objects.create(creator=chat_started_user, subscriber=writing_to)
        return Response({
            'room_id': room.id,
            'chat_started': chat_started_user.id,
            'chat_started_username': chat_started_user.username,
            'writing_to': writing_to.id,
            'writing_to_username': writing_to.username,
        }, status=status.HTTP_200_OK)


class LastMessagesAPIView(ListAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageListSerializer
    pagination_class = APILimitOffsetPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(room_id=self.kwargs['room_id'])
        return queryset
