from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.authentication.routes.auth import (LoginWelcomeAPIView, LoginVerifySMSAPIView, LoginSetUsernameAPIView,
                                             AuthAccountDataAPIView, JWTObtainPairView)

urlpatterns = [
    path('auth/login/welcome/', LoginWelcomeAPIView.as_view(), name='login_welcome'),
    path('auth/login/verify-sms/', LoginVerifySMSAPIView.as_view(), name='login_verify_sms'),
    path('auth/login/set-username/', LoginSetUsernameAPIView.as_view(), name='login_set_username'),
    path('auth/account-data/', AuthAccountDataAPIView.as_view(), name='auth_account_data'),

    path('admin-auth/token/', JWTObtainPairView.as_view(), name='token_obtain_pair'),
    path('admin-auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
