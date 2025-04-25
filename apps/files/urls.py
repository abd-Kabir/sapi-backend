from django.urls import path

from apps.files.views import FileCreateAPIView, FileDeleteAPIView

app_name = 'files'
urlpatterns = [
    path('create/', FileCreateAPIView.as_view(), name='file_create'),
    path('delete/<int:pk>/', FileDeleteAPIView.as_view(), name='file_delete'),
]
