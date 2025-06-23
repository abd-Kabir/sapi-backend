from django.urls import path

from apps.authentication.routes.admin import (AdminCreatorListAPIView, AdminCreatorSAPIShareAPIView,
                                              AdminCreatorRetrieveAPIView, AdminBlockCreatorAPIView)

urlpatterns = [
    path('admin/creators/', AdminCreatorListAPIView.as_view(), name='admin_creators'),
    path('admin/creator/<int:pk>/', AdminCreatorRetrieveAPIView.as_view(), name='admin_creator'),
    path('admin/creator/<int:pk>/sapi-share', AdminCreatorSAPIShareAPIView.as_view(), name='admin_creators_sapi_share'),
    path('admin/block-creator/', AdminBlockCreatorAPIView.as_view(), name='admin_block_creator'),
]
