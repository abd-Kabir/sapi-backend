from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.content.views import (PostCreateAPIView, CategoryModelViewSet, ChoiceTypeListAPIView,
                                PostAccessibilityAPIView, QuestionnairePostAnswerAPIView, PostByCategoryListAPIView,
                                PostToggleLikeAPIView)

router = DefaultRouter()
router.register('category', CategoryModelViewSet, basename='category')

app_name = 'content'
urlpatterns = [
    path('choices/', ChoiceTypeListAPIView.as_view(), name='choices'),
    path('post/create/', PostCreateAPIView.as_view(), name='post_create'),
    path('post/<int:pk>/accessibility/', PostAccessibilityAPIView.as_view(), name='post_accessibility'),
    path('questionnaire-post/answer/', QuestionnairePostAnswerAPIView.as_view(), name='questionnaire_post_answer'),

    path('post/by-category/', PostByCategoryListAPIView.as_view(), name='post_by_category'),
    path('post/toggle-like/', PostToggleLikeAPIView.as_view(), name='post_toggle_like'),
]
urlpatterns += router.urls
