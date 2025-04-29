from django.urls import path

from apps.authentication.routes.user import (BecomeUserMultibankAPIView, BecomeUserMultibankVerificationAPIView,
                                             BecomeCreatorAPIView, EditAccountAPIView, RetrieveAccountInfoAPIView)

urlpatterns = [
    path('user/become-creator/multibank/', BecomeUserMultibankAPIView.as_view(), name='become_creator_multibank'),
    path('user/become-creator/multibank-verification/', BecomeUserMultibankVerificationAPIView.as_view(),
         name='become_creator_multibank_verification'),
    path('user/become-creator/account/', BecomeCreatorAPIView.as_view(), name='become_creator_account'),
    path('user/edit-account/', EditAccountAPIView.as_view(), name='edit_account'),
    path('user/retrieve-account/', RetrieveAccountInfoAPIView.as_view(), name='retrieve_account'),
]
