from django.urls import path

from apps.authentication.routes.user import (BecomeUserMultibankAccountsAPIView, BecomeUserMultibankAddAccountAPIView,
                                             BecomeCreatorAPIView, ToggleFollowAPIView, UserRetrieveAPIView,
                                             UserSubscriptionPlanListAPIView, UserSubscribeCreateAPIView,
                                             PopularCreatorListAPIView, PopularCategoryCreatorListAPIView,
                                             SearchCreatorAPIView, ToggleBlockAPIView, DonateAPIView, GetMeAPIView,
                                             UserFundraisingListAPIView)

urlpatterns = [
    path('user/become-creator/multibank-accounts/', BecomeUserMultibankAccountsAPIView.as_view(),
         name='become_creator_multibank_accounts'),
    path('user/become-creator/multibank-add-account/', BecomeUserMultibankAddAccountAPIView.as_view(),
         name='become_creator_multibank_add_account'),
    path('user/become-creator/account/', BecomeCreatorAPIView.as_view(), name='become_creator_account'),

    path('user/<int:pk>/retrieve', UserRetrieveAPIView.as_view(), name='user_retrieve'),
    path('user/<int:user_id>/toggle-follow/', ToggleFollowAPIView.as_view(), name='follow_someone'),
    path('user/<int:user_id>/subscription-plan/list/', UserSubscriptionPlanListAPIView.as_view(),
         name='user_subscription_plan_list'),
    path('user/<int:user_id>/fundraising/list/', UserFundraisingListAPIView.as_view(),
         name='user_fundraising_plan_list'),
    path('user/subscribe/', UserSubscribeCreateAPIView.as_view(), name='user_subscribe'),
    path('user/popular-creators/', PopularCreatorListAPIView.as_view(), name='user_popular_creators'),
    path('user/popular-creators/<int:category_id>/by-category/', PopularCategoryCreatorListAPIView.as_view(),
         name='user_popular_creators_category'),
    path('user/search/creator/', SearchCreatorAPIView.as_view(), name='user_search_creator'),
    path('user/<int:user_id>/toggle-block/', ToggleBlockAPIView.as_view(), name='block_toggle'),
    path('user/donate/', DonateAPIView.as_view(), name='user_donate'),
    path('user/get-me/', GetMeAPIView.as_view(), name='user_get_me'),
]
