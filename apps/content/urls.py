from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.content.views import (PostCreateAPIView, CategoryModelViewSet, ChoiceTypeListAPIView)

router = DefaultRouter()
router.register('category', CategoryModelViewSet, basename='category')

app_name = 'content'
urlpatterns = [
    path('choices/', ChoiceTypeListAPIView.as_view(), name='choices'),
    path('post/create/', PostCreateAPIView.as_view(), name='post_create'),
]
urlpatterns += router.urls
