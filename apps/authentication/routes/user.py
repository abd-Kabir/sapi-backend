from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import RetrieveAPIView, ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import User, SubscriptionPlan, UserSubscription
from apps.authentication.serializers.user import BecomeCreatorSerializer, UserRetrieveSerializer, \
    UserSubscriptionPlanListSerializer, UserSubscriptionCreateSerializer
from config.core.api_exceptions import APIValidation


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


class UserRetrieveAPIView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserRetrieveSerializer


class ToggleFollowAPIView(APIView):
    """
    API to toggle follow/unfollow a user
    """

    @staticmethod
    def get_user(user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise APIValidation(_('Пользователь не найден'), status_code=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Success response",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='Operation status'),
                        'action': openapi.Schema(type=openapi.TYPE_STRING, description='Action performed'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'follower': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the follower'),
                                'followed': openapi.Schema(type=openapi.TYPE_INTEGER,
                                                           description='ID of the user being followed'),
                            },
                            description='Relationship data'
                        ),
                    }
                ),
                examples={
                    "application/json": {
                        "status": "success",
                        "action": "follow",  # or "unfollow" depending on the action
                        "data": {
                            "follower": 123,
                            "followed": 456,
                        }
                    }
                }
            ),
            # You can add other status codes and responses here
            400: "Bad Request",
            404: "Not Found",
        }
    )
    def post(self, request, user_id):
        # Get the user to be followed/unfollowed
        user_to_follow = self.get_user(user_id)
        follower = request.user

        # Can't follow yourself
        if follower == user_to_follow:
            return Response(
                {'detail': _('Вы не можете подписатся на себя.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if the follow relationship already exists
        action, follow_relation = follower.toggle_follow(user_to_follow)

        # Return the appropriate response
        return Response({
            'status': 'success',
            'action': action,
            'data': {
                'follower': follower.id,
                'followed': user_to_follow.id,
            }
        }, status=status.HTTP_200_OK)


class UserSubscriptionPlanListAPIView(ListAPIView):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = UserSubscriptionPlanListSerializer
    filter_backends = [OrderingFilter, ]
    ordering_fields = ['price']
    ordering = ['-price']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(creator=self.kwargs['user_id'])
        return queryset


class UserSubscribeCreateAPIView(CreateAPIView):
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionCreateSerializer
