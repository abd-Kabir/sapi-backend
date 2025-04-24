from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q



class AuthenticationBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user_model = get_user_model()
        try:
            if not username:
                username = kwargs.get('phone_number')
            if type(request) is WSGIRequest:
                user = user_model.objects.get(phone_number=username)
            else:
                user = user_model.objects.get(Q(phone_number=username), is_sms_verified=True)
        except user_model.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                return user
        return None
