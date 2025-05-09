from django.urls import path

from apps.authentication.routes.user import (BecomeUserMultibankAPIView, BecomeUserMultibankVerificationAPIView,
                                             BecomeCreatorAPIView, EditAccountAPIView, RetrieveAccountInfoAPIView,
                                             DeleteAccountAPIView, DeleteAccountVerifyAPIView, ToggleFollowAPIView,
                                             UserRetrieveAPIView, MyCardListAPIView, AddCardAPIView, DeleteCardAPIView,
                                             SetMainCardAPIView)

urlpatterns = [
    path('user/become-creator/multibank/', BecomeUserMultibankAPIView.as_view(), name='become_creator_multibank'),
    path('user/become-creator/multibank-verification/', BecomeUserMultibankVerificationAPIView.as_view(),
         name='become_creator_multibank_verification'),
    path('user/become-creator/account/', BecomeCreatorAPIView.as_view(), name='become_creator_account'),
    path('user/edit-account/', EditAccountAPIView.as_view(), name='edit_account'),
    path('user/retrieve-account/', RetrieveAccountInfoAPIView.as_view(), name='retrieve_account'),
    path('user/delete-account/', DeleteAccountAPIView.as_view(), name='delete_account'),
    path('user/delete-account-verification/', DeleteAccountVerifyAPIView.as_view(), name='delete_account_verification'),

    path('user/<int:pk>/retrieve', UserRetrieveAPIView.as_view(), name='user_retrieve'),
    path('user/<int:user_id>/toggle-follow/', ToggleFollowAPIView.as_view(), name='follow_someone'),

    path('user/card/own-list/', MyCardListAPIView.as_view(), name='user_my_card_list'),
    path('user/card/add-card/', AddCardAPIView.as_view(), name='user_add_card'),
    path('user/card/<int:pk>/delete-card/', DeleteCardAPIView.as_view(), name='user_delete_card'),
    path('user/card/<int:pk>/set-main/', SetMainCardAPIView.as_view(), name='user_set_main_card'),
]
