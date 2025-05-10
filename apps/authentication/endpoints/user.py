from django.urls import path

from apps.authentication.routes.user import (BecomeUserMultibankAPIView, BecomeUserMultibankVerificationAPIView,
                                             BecomeCreatorAPIView, ToggleFollowAPIView, UserRetrieveAPIView)

urlpatterns = [
    path('user/become-creator/multibank/', BecomeUserMultibankAPIView.as_view(), name='become_creator_multibank'),
    path('user/become-creator/multibank-verification/', BecomeUserMultibankVerificationAPIView.as_view(),
         name='become_creator_multibank_verification'),
    path('user/become-creator/account/', BecomeCreatorAPIView.as_view(), name='become_creator_account'),

    path('user/<int:pk>/retrieve', UserRetrieveAPIView.as_view(), name='user_retrieve'),
    path('user/<int:user_id>/toggle-follow/', ToggleFollowAPIView.as_view(), name='follow_someone'),

]
