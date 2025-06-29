from django.urls import path
from apps.authentication.routes.admin import (AdminCreatorListAPIView, AdminCreatorSAPIShareAPIView,
                                              AdminCreatorRetrieveAPIView, AdminBlockCreatorPostAPIView,
                                              AdminIgnoreReportAPIView, AdminBlockPostAPIView,
                                              AdminReportCommentAPIView, AdminUserCreationAPIView,
                                              AdminUserPermissionListAPIView, AdminUserListAPIView,
                                              AdminUserUpdateAPIView, AdminUserDeleteAPIView, ReportListView,
                                              ReportRetrieveAPIView, DashboardCreatorEarningsAPIView,
                                              AdminNotifDisListAPIView, AdminNotifDisCreateAPIView,
                                              AdminNotifDisUpdateAPIView)

urlpatterns = [
    # dashboard
    path('admin/dashboard-analytics/', DashboardCreatorEarningsAPIView.as_view(), name='admin_dashboard_analytics'),

    # --
    path('admin/block-creator-post/', AdminBlockCreatorPostAPIView.as_view(), name='admin_block_creator'),

    # creator page
    path('admin/creators/', AdminCreatorListAPIView.as_view(), name='admin_creators'),
    path('admin/creator/<int:pk>/', AdminCreatorRetrieveAPIView.as_view(), name='admin_creator'),
    path('admin/creator/<int:pk>/sapi-share', AdminCreatorSAPIShareAPIView.as_view(), name='admin_creators_sapi_share'),

    # report page
    path('admin/<int:report_id>/ignore-report/', AdminIgnoreReportAPIView.as_view(), name='admin_ignore_report'),
    path('admin/<int:report_id>/block-post/', AdminBlockPostAPIView.as_view(), name='admin_block_creator'),
    path('admin/<int:report_id>/add-report-comment/', AdminReportCommentAPIView.as_view(),
         name='admin_ignore_report_comment'),
    path('admin/reports/list/', ReportListView.as_view(), name='admin_list_reports'),
    path('admin/reports/<int:pk>/retrieve', ReportRetrieveAPIView.as_view(), name='admin_retrieve_post'),

    # admin user page
    path('admin/permission-list/', AdminUserPermissionListAPIView.as_view(), name='admin_permission_list'),
    path('admin/user-list/', AdminUserListAPIView.as_view(), name='admin_user_list'),
    path('admin/create-user/', AdminUserCreationAPIView.as_view(), name='admin_user_creation'),
    path('admin/update-user/<int:pk>/', AdminUserUpdateAPIView.as_view(), name='admin_user_update'),
    path('admin/delete-user/<int:pk>/', AdminUserDeleteAPIView.as_view(), name='admin_user_delete'),

    # notification distribution
    path('admin/notification-distribution/list/', AdminNotifDisListAPIView.as_view(), name='admin_notif_dis_list'),
    path('admin/notification-distribution/create/', AdminNotifDisCreateAPIView.as_view(),
         name='admin_notif_dis_create'),
    path('admin/notification-distribution/update/<int:pk>/', AdminNotifDisUpdateAPIView.as_view(),
         name='admin_notif_dis_update'),
]
