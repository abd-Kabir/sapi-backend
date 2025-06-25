from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.authentication.models import User
from apps.files.serializers import FileSerializer
from apps.integrations.services.sms_services import sms_confirmation_open, verify_sms_code, only_phone_numbers
from config.core.api_exceptions import APIValidation


class LoginWelcomeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=30, required=True)

    def validate(self, attrs):
        phone_number = only_phone_numbers(attrs.get('phone_number'))
        user, created = User.objects.get_or_create(phone_number=phone_number)
        user.is_active = False
        user.save()
        if created:
            sms_confirmation_open(user, 'register')
        else:
            sms_confirmation_open(user, 'login')
        return super().validate(attrs)


class LoginVerifySMSSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=30, required=True)
    code = serializers.CharField(max_length=30, required=True)

    @staticmethod
    def get_user(phone_number):
        try:
            return User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            raise APIValidation(_('Пользователь не найден'), status_code=status.HTTP_400_BAD_REQUEST)

    def validate(self, attrs):
        phone_number = only_phone_numbers(attrs.get('phone_number'))
        user = self.get_user(phone_number)
        sms = attrs.get('code')
        verify_sms_code(user, sms)
        return super().validate(attrs)


class LoginSetUsernameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username']


class AuthAccountDataSerializer(serializers.ModelSerializer):
    profile_photo = FileSerializer(read_only=True, allow_null=True)
    profile_banner_photo = FileSerializer(read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'phone_number',
            'is_creator',
            'profile_photo',
            'profile_banner_photo',
        ]


class JWTObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user, profile=None):
        user.last_login = timezone.now()
        token = super().get_token(user)
        # token['phone_number'] = user.phone_number
        user.save()
        return token


class JWTAdminLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField()
