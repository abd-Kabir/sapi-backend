from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from fcm_django.models import FCMDevice
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.integrations.api_integrations.firebase import register_device


class SendNotificationAPIView(APIView):

    def post(self, request):
        user = request.user
        title = request.data.get('title', 'Hello')
        body = request.data.get('body', 'You have a message')

        devices = FCMDevice.objects.filter(user=user)
        devices.send_message(title=title, body=body)

        return Response({'status': 'sent'})


class RegisterDeviceAPIView(APIView):

    @swagger_auto_schema(
        operation_summary='Register a device',
        operation_description='Registers a device for the authenticated user using the provided registration ID.',
        manual_parameters=[],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['registration_id'],
            properties={
                'registration_id': openapi.Schema(type=openapi.TYPE_STRING, description='Device registration ID'),
            },
        ),
        responses={200: openapi.Response('Device registered successfully', schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, example='registered')
            }
        ))}
    )
    def post(self, request):
        user = request.user
        registration_id = request.data.get('registration_id')
        register_device(user=user, registration_id=registration_id)
        return Response({'status': 'registered'})
