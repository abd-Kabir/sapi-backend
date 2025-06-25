from django.utils.timezone import now
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import User
from apps.authentication.serializers.auth import (LoginWelcomeSerializer, LoginVerifySMSSerializer,
                                                  LoginSetUsernameSerializer, AuthAccountDataSerializer,
                                                  JWTAdminLoginSerializer)
from apps.authentication.services import authenticate_user
from apps.integrations.services.sms_services import only_phone_numbers
from config.core.api_exceptions import APIValidation


class LoginWelcomeAPIView(APIView):
    permission_classes = [AllowAny, ]
    serializer_class = LoginWelcomeSerializer

    @staticmethod
    def get_user(phone_number):
        try:
            return User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            pass
            # raise APIValidation(_('Пользователь не найден'), status_code=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=LoginWelcomeSerializer)
    def post(self, request, *args, **kwargs):
        phone_number = only_phone_numbers(request.data.get('phone_number'))
        self.get_user(phone_number)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # data = serializer.validated_data
        return Response({'detail': _('СМС отправлен на указанный номер')})


class LoginVerifySMSAPIView(APIView):
    permission_classes = [AllowAny, ]
    serializer_class = LoginVerifySMSSerializer

    @staticmethod
    def get_user(phone_number):
        try:
            return User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            raise APIValidation(_('Пользователь не найден'), status_code=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=LoginVerifySMSSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        phone_number = only_phone_numbers(data['phone_number'])
        user = self.get_user(phone_number)
        user.is_sms_verified = True
        user.is_active = True
        user.last_login = now()
        user.save()
        refresh = RefreshToken.for_user(user)
        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return Response(tokens)


class LoginSetUsernameAPIView(APIView):
    serializer_class = LoginSetUsernameSerializer

    @swagger_auto_schema(request_body=LoginSetUsernameSerializer)
    def patch(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        user.username = data.get('username')
        user.save()
        return Response({'id': user.id, 'username': user.username})


class JWTObtainPairView(TokenObtainPairView):
    serializer_class = JWTAdminLoginSerializer
    permission_classes = [AllowAny, ]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            return Response(authenticate_user(request))
        else:
            raise APIValidation(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class AuthAccountDataAPIView(APIView):
    serializer_class = AuthAccountDataSerializer

    @swagger_auto_schema(operation_description='After login, get user account data',
                         responses={status.HTTP_200_OK: AuthAccountDataSerializer()})
    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(user)
        return Response(serializer.data)
