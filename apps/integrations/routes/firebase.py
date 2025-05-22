from fcm_django.models import FCMDevice
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.integrations.api_integrations.firebase import register_device


class SendNotificationAPIView(APIView):

    def post(self, request):
        user = request.user
        title = request.data.get("title", "Hello")
        body = request.data.get("body", "You have a message")

        devices = FCMDevice.objects.filter(user=user)
        devices.send_message(title=title, body=body)

        return Response({"status": "sent"})


class RegisterDeviceAPIView(APIView):

    def post(self, request):
        user = request.user
        registration_id = request.data.get("registration_id")
        register_device(user=user, registration_id=registration_id)
        return Response({"status": "registered"})
