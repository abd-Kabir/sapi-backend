from django.urls import path

from apps.authentication.views import (LoginWelcomeAPIView, LoginVerifySMSAPIView, LoginSetUsernameAPIView)

urlpatterns = [
    path('auth/login/welcome/', LoginWelcomeAPIView.as_view(), name='login_welcome'),
    path('auth/login/verify-sms/', LoginVerifySMSAPIView.as_view(), name='login_verify_sms'),
    path('auth/login/set-username/', LoginSetUsernameAPIView.as_view(), name='login_set_username'),

    # path('token/', JWTObtainPairView.as_view(), name='token_obtain_pair'),
    # path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
