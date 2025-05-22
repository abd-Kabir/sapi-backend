from django.urls import path

from apps.integrations.routes.firebase import SendNotificationAPIView, RegisterDeviceAPIView

urlpatterns = [
    # path('fcm/send-notifications-test/', SendNotificationAPIView.as_view(), name='fcm_send_notifications_test'),
    path('fcm/register-device/', RegisterDeviceAPIView.as_view(), name='fcm_register_device'),
]
