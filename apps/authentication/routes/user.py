from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _

from apps.authentication.serializers.user import BecomeCreatorSerializer, DeleteAccountVerifySerializer
from apps.integrations.services.sms_services import sms_confirmation_open


class BecomeUserMultibankAPIView(APIView):

    @swagger_auto_schema(operation_description="First step of becoming a creator, "
                                               "insert your Multibank account's number")
    def post(self, request, *args, **kwargs):
        return Response()


class BecomeUserMultibankVerificationAPIView(APIView):

    @swagger_auto_schema(operation_description='Second step of becoming a creator, Verify with sms')
    def post(self, request, *args, **kwargs):
        return Response()


class BecomeCreatorAPIView(APIView):
    serializer_class = BecomeCreatorSerializer

    @swagger_auto_schema(
        operation_description='Last step of becoming a creator, update your account data if you want',
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
        user.is_creator = True
        serializer.save()
        return Response(serializer.data)


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
