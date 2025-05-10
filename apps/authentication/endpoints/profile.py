from django.urls import path

from apps.authentication.routes.profile import (EditAccountAPIView, RetrieveAccountInfoAPIView, DeleteAccountAPIView,
                                                DeleteAccountVerifyAPIView, MyCardListAPIView, AddCardAPIView,
                                                DeleteCardAPIView, SetMainCardAPIView, MySubscriptionPlanListAPIView,
                                                AddSubscriptionPlanAPIView, MySubscriptionPlanRetrieveUpdateAPIView)

urlpatterns = [
    path('user/edit-account/', EditAccountAPIView.as_view(), name='edit_account'),
    path('user/retrieve-account/', RetrieveAccountInfoAPIView.as_view(), name='retrieve_account'),
    path('user/delete-account/', DeleteAccountAPIView.as_view(), name='delete_account'),
    path('user/delete-account-verification/', DeleteAccountVerifyAPIView.as_view(), name='delete_account_verification'),
    path('user/card/own-list/', MyCardListAPIView.as_view(), name='user_my_card_list'),
    path('user/card/add-card/', AddCardAPIView.as_view(), name='user_add_card'),
    path('user/card/<int:pk>/delete-card/', DeleteCardAPIView.as_view(), name='user_delete_card'),
    path('user/card/<int:pk>/set-main/', SetMainCardAPIView.as_view(), name='user_set_main_card'),

    path('user/subscription-plan/own-list/', MySubscriptionPlanListAPIView.as_view(),
         name='user_my_subscription-plan_list'),
    path('user/subscription-plan/add-subscription-plan/', AddSubscriptionPlanAPIView.as_view(),
         name='user_add_subscription_plan'),
    path('user/subscription-plan/<int:pk>/exact-subscription-plan/', MySubscriptionPlanRetrieveUpdateAPIView.as_view(),
         name='user_add_subscription_plan'),
]
