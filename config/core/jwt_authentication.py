from django.contrib.auth.models import AbstractBaseUser
from django.utils.translation import gettext_lazy as _


def replace_is_active_user_authentication_rule(user: AbstractBaseUser) -> bool:
    """
    Custom rule to check if the user can authenticate.
    Replace is_active=True with is_sms_verified=True.
    """
    return user is not None and user.is_sms_verified


from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model


class SAPIJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        """
        Override the get_user method to add custom validation for the user.
        """
        user_model = get_user_model()
        try:
            # Get the user from the token
            user_id = validated_token.payload.get('user_id')
            user = user_model.objects.get(**{'id': user_id})
        except user_model.DoesNotExist:
            raise AuthenticationFailed(_("Пользователь не найден"), code="user_not_found")

        # Custom validation: check `is_sms_verified` instead of `is_active`
        if not user.is_sms_verified:
            raise AuthenticationFailed(
                _("Пользователь неактивен (SMS не подтвержден)"),
                code="user_not_sms_verified"
            )

        return user
