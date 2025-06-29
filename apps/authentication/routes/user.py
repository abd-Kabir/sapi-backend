from django.db.models import Count, F
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import RetrieveAPIView, ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import User, SubscriptionPlan, UserSubscription, Donation, Fundraising
from apps.authentication.serializers.user import BecomeCreatorSerializer, UserRetrieveSerializer, \
    UserSubscriptionPlanListSerializer, UserSubscriptionCreateSerializer, DonationCreateSerializer, \
    BecomeUserMultibankAddAccountSerializer, UserFundraisingListSerializer
from apps.authentication.services import create_activity
from apps.content.models import Category
from apps.files.serializers import FileSerializer
from apps.integrations.api_integrations.multibank import multibank_prod_app
from config.core.api_exceptions import APIValidation
from config.swagger import query_search_swagger_param
from config.services import run_with_thread


class BecomeUserMultibankAccountsAPIView(APIView):

    @swagger_auto_schema(operation_description='First step of becoming a creator, '
                                               'List of your Multibank accounts.',
                         responses={200: openapi.Response(
                             description="List of creator's Multibank accounts.",
                             examples={
                                 'application/json': {
                                     'bank_accounts': [
                                         '22616000462176153001',
                                         '20206000762156286001'
                                     ]
                                 }
                             }
                         )})
    def get(self, request, *args, **kwargs):
        user = request.user
        account_data, m_status_code = multibank_prod_app.check_account(phone=user.phone_number)
        response = []
        if str(m_status_code).startswith('2'):
            accounts = account_data.get('data', {}).get('accounts', [])
            pinfl = account_data.get('data', {}).get('user', {}).get('pinfl')
            user.pinfl = pinfl
            user.save(update_fields=['pinfl'])
            for acc in accounts:
                if acc.get('type') != 'tirikchilik':
                    continue
                response.append(acc.get('account'))
            return Response({'bank_accounts': response})
        return Response(account_data, status=m_status_code)


class BecomeUserMultibankAddAccountAPIView(APIView):
    serializer_class = BecomeUserMultibankAddAccountSerializer

    @swagger_auto_schema(operation_description='Second step of becoming a creator, select one of multibank account.',
                         request_body=BecomeUserMultibankAddAccountSerializer)
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        account_data, m_status_code = multibank_prod_app.check_account(phone=user.phone_number)
        bank_accounts = []
        if str(m_status_code).startswith('2'):
            accounts = account_data.get('data', {}).get('accounts', [])
            for acc in accounts:
                if acc.get('type') != 'tirikchilik':
                    continue
                bank_accounts.append(acc.get('account'))
        if not data.get('multibank_account') in bank_accounts:
            raise APIValidation(_('Введите действующий номер аккаунта.'), status_code=status.HTTP_400_BAD_REQUEST)
        user.multibank_account = data.get('multibank_account')
        user.multibank_verified = True
        user.save(update_fields=['multibank_account', 'multibank_verified'])
        return Response({'user_id': user.id, 'multibank_account': user.multibank_account})


class BecomeCreatorAPIView(APIView):
    serializer_class = BecomeCreatorSerializer

    @swagger_auto_schema(
        operation_description='Last step of becoming a creator, update your account data if you want',
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=[], properties={
            'category': openapi.Schema(type=openapi.TYPE_INTEGER),
            'username': openapi.Schema(type=openapi.TYPE_STRING),
            'creator_description': openapi.Schema(type=openapi.TYPE_STRING),
            'profile_photo': openapi.Schema(type=openapi.TYPE_INTEGER),
            'profile_banner_photo': openapi.Schema(type=openapi.TYPE_INTEGER),
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
        if action == 'followed':
            run_with_thread(create_activity, ('followed', None, None, follower, user_to_follow))

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


class UserFundraisingListAPIView(ListAPIView):
    queryset = Fundraising.objects.all()
    serializer_class = UserFundraisingListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(creator=self.kwargs['user_id'])
        return queryset


class UserSubscribeCreateAPIView(CreateAPIView):
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionCreateSerializer


class PopularCreatorListAPIView(APIView):

    def most_popular_creators(self, limit: int = 10):
        return (
            User.objects
            .filter(is_creator=True)
            .annotate(follower_count=Count('followers'))
            .order_by('-follower_count')
            .values('id', 'username', 'follower_count', profile_photo_path=F('profile_photo__path'))
            [:limit]
        )

    def popular_creators_by_category(self, limit_per_category: int = 5):
        from django.db.models import Count

        categories_with_creators = Category.objects.filter(
            users__is_creator=True,
            users__is_deleted=False
        ).distinct()

        result = []

        for category in categories_with_creators:
            creators = (
                User.objects
                .filter(category=category, is_creator=True)
                .annotate(follower_count=Count('followers'))
                .order_by('-follower_count')
                .values('id', 'username', 'follower_count', profile_photo_path=F('profile_photo__path'))
                [:limit_per_category]
            )
            if creators:
                result.append({
                    'category_id': category.id,
                    'category_name': category.name,
                    'creators': creators,
                })
        return result

    @swagger_auto_schema(
        operation_description="Get most popular creators and popular creators by categories",
        responses={
            200: openapi.Response(
                description="Popular creators data",
                examples={
                    "application/json": {
                        "most_populars": [
                            {
                                "id": 1,
                                "username": "umarov",
                                "follower_count": 1,
                                "profile_photo_path": "media/uploads/17464402879838739793815586f6f31465a94653c44aa5cfca1.jpg"
                            }
                        ],
                        "popular_by_categories": [
                            {
                                "category_id": 1,
                                "category_name": "Music",
                                "creators": [
                                    {
                                        "id": 1,
                                        "username": "umarov",
                                        "follower_count": 1,
                                        "profile_photo_path": "media/uploads/17464402879838739793815586f6f31465a94653c44aa5cfca1.jpg"
                                    }
                                ]
                            }
                        ]
                    }
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        most_populars = self.most_popular_creators()
        most_populars_by_category = self.popular_creators_by_category()
        return Response({
            'most_populars': most_populars,
            'popular_by_categories': most_populars_by_category
        })


class PopularCategoryCreatorListAPIView(APIView):

    def most_popular_creators(self, category_id, limit: int = 10):
        return (
            User.objects
            .filter(is_creator=True, category_id=category_id)
            .annotate(follower_count=Count('followers'))
            .order_by('-follower_count')
            .values('id', 'username', 'follower_count', profile_photo_path=F('profile_photo__path'))
            [:limit]
        )

    def popular_creators_by_category(self, category_id, limit_per_category: int = 5):
        from django.db.models import Count

        categories_with_creators = Category.objects.filter(
            users__is_creator=True,
            users__is_deleted=False,
            pk=category_id
        ).distinct()

        if categories_with_creators.exists():
            category = categories_with_creators.first()
            creators = (
                User.objects
                .filter(category=category, is_creator=True)
                .annotate(follower_count=Count('followers'))
                .order_by('-follower_count')
                .values('id', 'username', 'follower_count', profile_photo_path=F('profile_photo__path'))
                [:limit_per_category]
            )
            return {
                'category_id': category.id,
                'category_name': category.name,
                'creators': creators,
            }
        else:
            return {}

    @swagger_auto_schema(
        operation_description="Get popular creators",
        responses={
            200: openapi.Response(
                description="Popular creators data",
                examples={
                    "application/json": {
                        "most_populars": [
                            {
                                "id": 1,
                                "username": "umarov",
                                "follower_count": 1,
                                "profile_photo_path": "media/uploads/17464402879838739793815586f6f31465a94653c44aa5cfca1.jpg"
                            }
                        ],
                        "popular_by_category": {
                            "category_id": 1,
                            "category_name": "Music",
                            "creators": [
                                {
                                    "id": 1,
                                    "username": "umarov",
                                    "follower_count": 1,
                                    "profile_photo_path": "media/uploads/17464402879838739793815586f6f31465a94653c44aa5cfca1.jpg"
                                }
                            ]
                        }
                    }
                }
            )
        }
    )
    def get(self, request, category_id, *args, **kwargs):
        most_populars = self.most_popular_creators(category_id=category_id)
        most_populars_by_category = self.popular_creators_by_category(category_id)
        return Response({
            'most_populars': most_populars,
            'popular_by_category': most_populars_by_category
        })


class SearchCreatorAPIView(APIView):
    @swagger_auto_schema(
        manual_parameters=[query_search_swagger_param],
        responses={
            200: openapi.Response(
                description="Popular creators data",
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "username": "umarov",
                            "follower_count": 1,
                            "profile_photo_path": "media/uploads/17464402879838739793815586f6f31465a94653c44aa5cfca1.jpg"
                        }
                    ]
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        search_term = request.GET.get('search')
        if not search_term:
            return Response([])
        users = (
            User.objects
            .annotate(follower_count=Count('followers'))
            .filter(is_creator=True, username__icontains=search_term)
            .values('id', 'username', 'follower_count', profile_photo_path=F('profile_photo__path'))
            .order_by('-follower_count')
            [:15]
        )
        return Response(users)


class ToggleBlockAPIView(APIView):
    """
    API to toggle block/unblock a user
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
                                'blocker': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the blocker'),
                                'blocked': openapi.Schema(type=openapi.TYPE_INTEGER,
                                                          description='ID of the user being blocked'),
                            },
                            description='Relationship data'
                        ),
                    }
                ),
                examples={
                    "application/json": {
                        "status": "success",
                        "action": "block",  # or "unblock" depending on the action
                        "data": {
                            "blocker": 123,
                            "blocked": 456,
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
        # Get the user to be blocked/unblocked
        user_to_block = self.get_user(user_id)
        blocker = request.user

        # Can't block yourself
        if blocker == user_to_block:
            return Response(
                {'detail': _('Вы не можете заблокировать себя.')},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if the block relationship already exists
        action, toggle_relation = blocker.toggle_block(user_to_block)

        # Return the appropriate response
        return Response({
            'status': 'success',
            'action': action,
            'data': {
                'blocker': blocker.id,
                'blocked': user_to_block.id,
            }
        }, status=status.HTTP_200_OK)


class DonateAPIView(CreateAPIView):
    queryset = Donation.objects.all()
    serializer_class = DonationCreateSerializer

    @swagger_auto_schema(
        request_body=DonationCreateSerializer,
        responses={
            201: openapi.Response(
                description='Donation created successfully',
                schema=DonationCreateSerializer,
                examples={
                    'application/json': {
                        'amount': 10000,
                        'message': None,
                        'card': 12,
                        'fundraising': None,
                        'creator': 1,
                        'payment_info': {
                            'need_otp': False,
                            'transaction_id': '9bf2385d-46a1-11f0-bdd5-005056b4367d'
                        }
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class GetMeAPIView(APIView):
    @staticmethod
    def serialize_file(file):
        return FileSerializer(file).data if file else None

    @swagger_auto_schema(
        responses={
            201: openapi.Response(
                description='Get data of authorized user.',
                examples={
                    'application/json': {
                        "user_id": 1,
                        "is_creator": True,
                        "username": "ukabir",
                        "phone_number": "998909903929",
                        "profile_photo": {
                            "name": "3. Леопард.jpg",
                            "size": 2083432,
                            "path": "media/uploads/17477393637271354228422af39d5b742b7918d3ad7e5d23c17.jpg"
                        },
                        "banner_photo": {
                            "name": "3. Леопард.jpg",
                            "size": 2083432,
                            "path": "media/uploads/17477393637271354228422af39d5b742b7918d3ad7e5d23c17.jpg"
                        },
                        "category_id": 1,
                        "category_name": "Test",
                        "multibank_account": "22616000462176153001",
                        "multibank_verified": True
                    }
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        user: User = request.user

        return Response({
            'user_id': user.id,
            'is_creator': user.is_creator,
            'username': user.username,
            'phone_number': user.phone_number,
            'profile_photo': self.serialize_file(user.profile_photo),
            'banner_photo': self.serialize_file(user.profile_banner_photo),
            'category_id': user.category_id,
            'category_name': user.category.name if user.category else None,
            'multibank_account': user.multibank_account,
            'multibank_verified': user.multibank_verified,
        })
