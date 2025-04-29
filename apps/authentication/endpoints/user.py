from django.urls import path

from apps.authentication.routes.user import BecomeUserMultibankAPIView, BecomeUserMultibankVerificationAPIView

urlpatterns = [
    path('become-user/multibank/', BecomeUserMultibankAPIView.as_view(), name='become_user_multibank'),
    path('become-user/multibank-verification/', BecomeUserMultibankVerificationAPIView.as_view(),
         name='become_user_multibank_verification'),
    path('become-user/multibank-verification/', BecomeUserMultibankVerificationAPIView.as_view(),
         name='become_user_multibank_verification'),
]
