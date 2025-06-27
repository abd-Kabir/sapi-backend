from fcm_django.models import FCMDevice


def send_notification_to_user(user, title, body):
    devices = FCMDevice.objects.filter(user=user)
    devices.send_message(
        # title=title,
        # body=body,
        message={
            "title": title,
            "body": body,
        },
        data={"click_action": "FLUTTER_NOTIFICATION_CLICK"}  # required for foreground notifications
    )


def register_device(user, registration_id, device_type='android'):
    device, created = FCMDevice.objects.get_or_create(
        registration_id=registration_id,
        defaults={'user': user, 'type': device_type},
    )
    if not created:
        device.user = user
        device.save()
