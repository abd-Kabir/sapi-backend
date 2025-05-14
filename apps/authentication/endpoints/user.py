from django.urls import path

from apps.authentication.routes.user import (BecomeUserMultibankAPIView, BecomeUserMultibankVerificationAPIView,
                                             BecomeCreatorAPIView, ToggleFollowAPIView, UserRetrieveAPIView,
                                             UserSubscriptionPlanListAPIView, UserSubscribeCreateAPIView,
                                             PopularCreatorListAPIView, PopularCategoryCreatorListAPIView,
                                             SearchCreatorAPIView)

urlpatterns = [
    path('user/become-creator/multibank/', BecomeUserMultibankAPIView.as_view(), name='become_creator_multibank'),
    path('user/become-creator/multibank-verification/', BecomeUserMultibankVerificationAPIView.as_view(),
         name='become_creator_multibank_verification'),
    path('user/become-creator/account/', BecomeCreatorAPIView.as_view(), name='become_creator_account'),

    path('user/<int:pk>/retrieve', UserRetrieveAPIView.as_view(), name='user_retrieve'),
    path('user/<int:user_id>/toggle-follow/', ToggleFollowAPIView.as_view(), name='follow_someone'),
    path('user/<int:user_id>/subscription-plan/list/', UserSubscriptionPlanListAPIView.as_view(),
         name='user_subscription_plan_list'),
    path('user/subscribe/', UserSubscribeCreateAPIView.as_view(), name='user_subscribe'),
    path('user/popular-creators/', PopularCreatorListAPIView.as_view(), name='user_popular_creators'),
    path('user/popular-creators/<int:category_id>/by-category/', PopularCategoryCreatorListAPIView.as_view(),
         name='user_popular_creators_category'),
    path('user/search/creator/', SearchCreatorAPIView.as_view(), name='user_search_creator'),
]
