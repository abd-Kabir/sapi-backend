from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.serializers.user import BecomeCreatorSerializer


class BecomeUserMultibankAPIView(APIView):

    @swagger_auto_schema(operation_description="First step of becoming a creator, "
                                               "insert your Multibank account's number")
    def post(self, request, *args, **kwargs):
        return Response()


class BecomeUserMultibankVerificationAPIView(APIView):

    @swagger_auto_schema(operation_description='Second step of becoming a creator, Verify with sms')
    def post(self, request, *args, **kwargs):
        return Response()


class BecomeCreatorAPIView(APIView):
    serializer_class = BecomeCreatorSerializer

    @swagger_auto_schema(
        operation_description='Last step of becoming a creator, update your account data if you want',
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=[], properties={
            'category': openapi.Schema(type=openapi.TYPE_INTEGER),
            'username': openapi.Schema(type=openapi.TYPE_STRING),
            'creator_description': openapi.Schema(type=openapi.TYPE_STRING),
            'profile_photo': openapi.Schema(type=openapi.TYPE_STRING),
            'profile_banner_photo': openapi.Schema(type=openapi.TYPE_STRING),
        }),
        responses={status.HTTP_201_CREATED: BecomeCreatorSerializer()}
    )
    def patch(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        user = request.user
        serializer = self.serializer_class(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user.is_creator = True
        serializer.save()
        return Response(serializer.data)


class EditAccountAPIView(APIView):
    serializer_class = BecomeCreatorSerializer

    @swagger_auto_schema(
        operation_description='API for editing account data',
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=[], properties={
            'category': openapi.Schema(type=openapi.TYPE_INTEGER),
            'username': openapi.Schema(type=openapi.TYPE_STRING),
            'creator_description': openapi.Schema(type=openapi.TYPE_STRING),
            'profile_photo': openapi.Schema(type=openapi.TYPE_STRING),
            'profile_banner_photo': openapi.Schema(type=openapi.TYPE_STRING),
        }),
        responses={status.HTTP_201_CREATED: BecomeCreatorSerializer()}
    )
    def patch(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        user = request.user
        serializer = self.serializer_class(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class RetrieveAccountInfoAPIView(APIView):
    serializer_class = BecomeCreatorSerializer

    @swagger_auto_schema(operation_description='Get user account data',
                         responses={status.HTTP_200_OK: BecomeCreatorSerializer()})
    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(user)
        return Response(serializer.data)
