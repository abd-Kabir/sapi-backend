from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message, Notification


def send_notification_to_user(user, title, body):
    devices = FCMDevice.objects.filter(user=user)
    devices.send_message(
        Message(notification=Notification(title=title, body=body))
    )


def register_device(user, registration_id, device_type='android'):
    device, created = FCMDevice.objects.get_or_create(
        registration_id=registration_id,
        defaults={'user': user, 'type': device_type},
    )
    if not created:
        device.user = user
        device.save()
