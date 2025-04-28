from django.urls import path

from apps.content.views import (PostCreateAPIView, CategoryListAPIView, ChoiceTypeListAPIView)

app_name = 'content'
urlpatterns = [
    path('choices/', ChoiceTypeListAPIView.as_view(), name='choices'),
    path('cateogory/list/', CategoryListAPIView.as_view(), name='category_list'),
    path('post/create/', PostCreateAPIView.as_view(), name='post_create'),
]
