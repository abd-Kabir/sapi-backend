from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView, ListAPIView, DestroyAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import Card, SubscriptionPlan
from apps.authentication.serializers.profile import (DeleteAccountVerifySerializer,
                                                     MyCardListSerializer, AddCardSerializer,
                                                     MySubscriptionPlanListSerializer, AddSubscriptionPlanSerializer,
                                                     MySubscriptionPlanRetrieveUpdateSerializer)
from apps.authentication.serializers.user import BecomeCreatorSerializer
from apps.content.models import Post
from apps.content.serializers import PostListSerializer
from apps.integrations.services.sms_services import sms_confirmation_open
from config.core.api_exceptions import APIValidation
from config.core.pagination import APILimitOffsetPagination
from config.core.permissions import IsCreator


class EditAccountAPIView(APIView):
    serializer_class = BecomeCreatorSerializer

    @swagger_auto_schema(
        operation_description='API for editing account data',
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=[], properties={
            'category': openapi.Schema(type=openapi.TYPE_INTEGER),
            'username': openapi.Schema(type=openapi.TYPE_STRING),
            'creator_description': openapi.Schema(type=openapi.TYPE_STRING),
            'profile_photo': openapi.Schema(type=openapi.TYPE_STRING),
            'profile_banner_photo': openapi.Schema(type=openapi.TYPE_STRING),
        }),
        responses={status.HTTP_201_CREATED: BecomeCreatorSerializer()}
    )
    def patch(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        user = request.user
        serializer = self.serializer_class(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class RetrieveAccountInfoAPIView(APIView):
    serializer_class = BecomeCreatorSerializer

    @swagger_auto_schema(operation_description='Get user account data',
                         responses={status.HTTP_200_OK: BecomeCreatorSerializer()})
    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(user)
        return Response(serializer.data)


class DeleteAccountAPIView(APIView):

    @swagger_auto_schema(
        operation_description='Delete Account API',
        responses={
            status.HTTP_200_OK: openapi.Response(
                description=_('СМС отправлен на указанный номер'),
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'detail': openapi.Schema(
                    type=openapi.TYPE_STRING, example=_('СМС отправлен на указанный номер')
                )}))
        }
    )
    def delete(self, request, *args, **kwargs):
        user = request.user
        sms_confirmation_open(user, 'delete_account')
        return Response({'detail': _('СМС отправлен на указанный номер')})


class DeleteAccountVerifyAPIView(APIView):
    serializer_class = DeleteAccountVerifySerializer

    @swagger_auto_schema(
        operation_description='Delete Account Verification API',
        request_body=DeleteAccountVerifySerializer,
        responses={
            status.HTTP_200_OK: openapi.Response(
                description=_('Ваш аккаунт удален'),
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'detail': openapi.Schema(
                    type=openapi.TYPE_STRING, example=_('Ваш аккаунт удален')
                )}))
        }
    )
    def delete(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user.is_active = False
        user.is_deleted = True
        user.save()
        return Response({'detail': _('Ваш аккаунт удален')})


class MyCardListAPIView(ListAPIView):
    queryset = Card.objects.all()
    serializer_class = MyCardListSerializer
    permission_classes = [IsCreator, ]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        queryset = queryset.filter(user=user)
        return queryset


class AddCardAPIView(CreateAPIView):
    queryset = Card.objects.all()
    serializer_class = AddCardSerializer
    permission_classes = [IsCreator, ]


class DeleteCardAPIView(DestroyAPIView):
    queryset = Card.objects.all()
    permission_classes = [IsCreator, ]

    def destroy(self, request, *args, **kwargs):
        user = request.user
        instance: Card = self.get_object()
        if instance.user != user:
            raise APIValidation(_('Карта не найдена'), status_code=status.HTTP_404_NOT_FOUND)
        # self.perform_destroy(instance)
        instance.is_deleted = True
        instance.delete_card()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SetMainCardAPIView(APIView):
    queryset = Card.objects.all()
    permission_classes = [IsCreator, ]

    @staticmethod
    def get_card(pk):
        try:
            return Card.objects.get(pk=pk)
        except Card.DoesNotExist:
            raise APIValidation(_('Карта не найдена'), status_code=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk, *args, **kwargs):
        user = request.user
        instance: Card = self.get_card(pk)
        if instance.user != user:
            raise APIValidation(_('Карта не найдена'), status_code=status.HTTP_404_NOT_FOUND)
        # self.perform_destroy(instance)
        instance.set_main(True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MySubscriptionPlanListAPIView(ListAPIView):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = MySubscriptionPlanListSerializer
    permission_classes = [IsCreator, ]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        queryset = queryset.filter(creator=user)
        return queryset


class AddSubscriptionPlanAPIView(CreateAPIView):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = AddSubscriptionPlanSerializer
    permission_classes = [IsCreator, ]


class MySubscriptionPlanRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = MySubscriptionPlanRetrieveUpdateSerializer
    permission_classes = [IsCreator, ]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        queryset = queryset.filter(creator=user)
        return queryset


class LikedPostListAPIView(ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostListSerializer
    pagination_class = APILimitOffsetPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        queryset = queryset.filter(likes__user=user)
        return queryset


class SavedPostListAPIView(ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostListSerializer
    pagination_class = APILimitOffsetPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        queryset = queryset.filter(saved_by_users__user=user)
        return queryset
