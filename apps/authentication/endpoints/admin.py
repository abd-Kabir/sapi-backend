from django.urls import path
from apps.authentication.routes.admin import (AdminCreatorListAPIView, AdminCreatorSAPIShareAPIView,
                                              AdminCreatorRetrieveAPIView, AdminBlockCreatorAPIView,
                                              AdminIgnoreReportAPIView, AdminBlockPostAPIView,
                                              AdminReportCommentAPIView, AdminUserCreationAPIView,
                                              AdminUserPermissionListAPIView, AdminUserListAPIView,
                                              AdminUserUpdateAPIView, AdminUserDeleteAPIView)

urlpatterns = [
    path('admin/block-creator/', AdminBlockCreatorAPIView.as_view(), name='admin_block_creator'),

    # creator page
    path('admin/creators/', AdminCreatorListAPIView.as_view(), name='admin_creators'),
    path('admin/creator/<int:pk>/', AdminCreatorRetrieveAPIView.as_view(), name='admin_creator'),
    path('admin/creator/<int:pk>/sapi-share', AdminCreatorSAPIShareAPIView.as_view(), name='admin_creators_sapi_share'),

    # report page
    path('admin/<int:report_id>/ignore-report/', AdminIgnoreReportAPIView.as_view(), name='admin_ignore_report'),
    path('admin/<int:report_id>/block-post/', AdminBlockPostAPIView.as_view(), name='admin_block_creator'),
    path('admin/<int:report_id>/add-report-comment/', AdminReportCommentAPIView.as_view(),
         name='admin_ignore_report_comment'),

    # admin user page
    path('admin/permission-list/', AdminUserPermissionListAPIView.as_view(), name='admin_permission_list'),
    path('admin/user-list/', AdminUserListAPIView.as_view(), name='admin_user_list'),
    path('admin/create-user/', AdminUserCreationAPIView.as_view(), name='admin_user_creation'),
    path('admin/update-user/<int:pk>/', AdminUserUpdateAPIView.as_view(), name='admin_user_update'),
    path('admin/delete-user/<int:pk>/', AdminUserDeleteAPIView.as_view(), name='admin_user_delete'),
]
