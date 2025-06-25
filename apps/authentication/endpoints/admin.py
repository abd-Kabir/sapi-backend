from django.urls import path

from apps.authentication.routes.admin import (AdminCreatorListAPIView, AdminCreatorSAPIShareAPIView,
                                              AdminCreatorRetrieveAPIView, AdminBlockCreatorAPIView,
                                              AdminIgnoreReportAPIView, AdminBlockPostAPIView,
                                              AdminReportCommentAPIView)

urlpatterns = [
    path('admin/creators/', AdminCreatorListAPIView.as_view(), name='admin_creators'),
    path('admin/creator/<int:pk>/', AdminCreatorRetrieveAPIView.as_view(), name='admin_creator'),
    path('admin/creator/<int:pk>/sapi-share', AdminCreatorSAPIShareAPIView.as_view(), name='admin_creators_sapi_share'),
    path('admin/block-creator/', AdminBlockCreatorAPIView.as_view(), name='admin_block_creator'),
    path('admin/<int:post_id>/ignore-report/', AdminIgnoreReportAPIView.as_view(), name='admin_ignore_report'),
    path('admin/<int:post_id>/block-post/', AdminBlockPostAPIView.as_view(), name='admin_block_creator'),
    path('admin/<int:post_id>/add-report-comment/', AdminReportCommentAPIView.as_view(), name='admin_ignore_report_comment'),
]
