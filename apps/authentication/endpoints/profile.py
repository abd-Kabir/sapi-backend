from django.urls import path

from apps.authentication.routes.profile import (EditAccountAPIView, RetrieveAccountInfoAPIView, DeleteAccountAPIView,
                                                DeleteAccountVerifyAPIView, MyCardListAPIView, AddCardAPIView,
                                                DeleteCardAPIView, SetMainCardAPIView, MySubscriptionPlanListAPIView,
                                                AddSubscriptionPlanAPIView, MySubscriptionPlanRetrieveUpdateAPIView,
                                                LikedPostListAPIView, SavedPostListAPIView,
                                                FundraisingListCreateAPIView, FundraisingDeleteRetrieveUpdateAPIView,
                                                FollowersDashboardAPIView, FollowersDashboardByPlanAPIView)

urlpatterns = [
    # account
    path('profile/edit-account/', EditAccountAPIView.as_view(), name='edit_account'),
    path('profile/retrieve-account/', RetrieveAccountInfoAPIView.as_view(), name='retrieve_account'),
    path('profile/delete-account/', DeleteAccountAPIView.as_view(), name='delete_account'),
    path('profile/delete-account-verification/', DeleteAccountVerifyAPIView.as_view(),
         name='delete_account_verification'),

    # cards
    path('profile/card/own-list/', MyCardListAPIView.as_view(), name='profile_my_card_list'),
    path('profile/card/add-card/', AddCardAPIView.as_view(), name='profile_add_card'),
    path('profile/card/<int:pk>/delete-card/', DeleteCardAPIView.as_view(), name='profile_delete_card'),
    path('profile/card/<int:pk>/set-main/', SetMainCardAPIView.as_view(), name='profile_set_main_card'),

    # subscription-plans
    path('profile/subscription-plan/own-list/', MySubscriptionPlanListAPIView.as_view(),
         name='profile_my_subscription-plan_list'),
    path('profile/subscription-plan/add-subscription-plan/', AddSubscriptionPlanAPIView.as_view(),
         name='profile_add_subscription_plan'),
    path('profile/subscription-plan/<int:pk>/exact-subscription-plan/',
         MySubscriptionPlanRetrieveUpdateAPIView.as_view(),
         name='profile_add_subscription_plan'),

    # saved/liked posts
    path('profile/interested/liked-posts/', LikedPostListAPIView.as_view(), name='own_liked_posts'),
    path('profile/interested/saved-posts/', SavedPostListAPIView.as_view(), name='own_saved_posts'),

    # fundraising
    path('profile/fundraising/', FundraisingListCreateAPIView.as_view(), name='profile_fundraising_list_create'),
    path('profile/fundraising/<int:pk>/', FundraisingDeleteRetrieveUpdateAPIView.as_view(),
         name='profile_fundraising_get_destroy_update'),

    # dashboard
    path('profile/dashboard/followers/', FollowersDashboardAPIView.as_view(), name='profile_dashboard_followers'),
    path('profile/dashboard/followers-by-plan/', FollowersDashboardByPlanAPIView.as_view(), name='profile_dashboard_by_plan'),
]
