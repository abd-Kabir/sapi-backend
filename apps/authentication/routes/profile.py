from collections import defaultdict, OrderedDict
from datetime import timedelta

from django.conf import settings
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils.timezone import now, localtime
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView, ListAPIView, DestroyAPIView, RetrieveUpdateAPIView, \
    ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import Card, SubscriptionPlan, Fundraising, UserFollow
from apps.authentication.serializers.profile import (DeleteAccountVerifySerializer,
                                                     MyCardListSerializer, AddCardSerializer,
                                                     MySubscriptionPlanListSerializer, AddSubscriptionPlanSerializer,
                                                     MySubscriptionPlanRetrieveUpdateSerializer,
                                                     FundraisingSerializer, FollowersDashboardByPlanSerializer)
from apps.authentication.serializers.user import BecomeCreatorSerializer
from apps.content.models import Post
from apps.content.serializers import PostListSerializer
from apps.integrations.api_integrations.multibank import multibank_prod_app
from apps.integrations.services.sms_services import sms_confirmation_open
from config.core.api_exceptions import APIValidation
from config.core.pagination import APILimitOffsetPagination
from config.core.permissions import IsCreator


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


class DeleteAccountAPIView(APIView):

    @swagger_auto_schema(
        operation_description='Delete Account API',
        responses={
            status.HTTP_200_OK: openapi.Response(
                description=_('СМС отправлен на указанный номер'),
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'detail': openapi.Schema(
                    type=openapi.TYPE_STRING, example=_('СМС отправлен на указанный номер')
                )}))
        }
    )
    def delete(self, request, *args, **kwargs):
        user = request.user
        sms_confirmation_open(user, 'delete_account')
        return Response({'detail': _('СМС отправлен на указанный номер')})


class DeleteAccountVerifyAPIView(APIView):
    serializer_class = DeleteAccountVerifySerializer

    @swagger_auto_schema(
        operation_description='Delete Account Verification API',
        request_body=DeleteAccountVerifySerializer,
        responses={
            status.HTTP_200_OK: openapi.Response(
                description=_('Ваш аккаунт удален'),
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'detail': openapi.Schema(
                    type=openapi.TYPE_STRING, example=_('Ваш аккаунт удален')
                )}))
        }
    )
    def delete(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user.temp_phone_number = user.phone_number
        user.phone_number = None
        user.temp_username = user.username
        user.username = None
        user.is_active = False
        user.is_deleted = True
        user.save()
        return Response({'detail': _('Ваш аккаунт удален')})


class MyCardListAPIView(ListAPIView):
    queryset = Card.objects.all()
    serializer_class = MyCardListSerializer

    # permission_classes = [IsCreator, ]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        queryset = queryset.filter(user=user)
        return queryset


class AddCardAPIView(CreateAPIView):
    queryset = Card.objects.all()
    serializer_class = AddCardSerializer

    def create(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        multibank_response, m_bank_status = multibank_prod_app.bind_card(
            data={
                'store_id': settings.MULTIBANK_INTEGRATION_SETTINGS['PROD']['STORE_ID'],
                'callback_url': 'https://api.sapi.uz/api/multibank/bind-card/webhook/',
                'phone': user.phone_number
            }
        )
        if str(m_bank_status).startswith('2'):
            bind_card_url = multibank_response.get('data', {}).get('form_url')
            return Response({'bind_card_url': bind_card_url}, headers=headers)
        return Response(multibank_response, status=m_bank_status)


class DeleteCardAPIView(DestroyAPIView):
    queryset = Card.objects.all()

    # permission_classes = [IsCreator, ]

    def destroy(self, request, *args, **kwargs):
        user = request.user
        instance: Card = self.get_object()
        if instance.user != user:
            raise APIValidation(_('Карта не найдена'), status_code=status.HTTP_404_NOT_FOUND)
        # self.perform_destroy(instance)
        if instance.token:
            multibank_prod_app.remove_card(card_token=instance.token)
        instance.delete_card()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SetMainCardAPIView(APIView):
    queryset = Card.objects.all()
    permission_classes = [IsCreator, ]

    @staticmethod
    def get_card(pk):
        try:
            return Card.objects.get(pk=pk)
        except Card.DoesNotExist:
            raise APIValidation(_('Карта не найдена'), status_code=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk, *args, **kwargs):
        user = request.user
        instance: Card = self.get_card(pk)
        if instance.user != user:
            raise APIValidation(_('Карта не найдена'), status_code=status.HTTP_404_NOT_FOUND)
        # self.perform_destroy(instance)
        instance.set_main(True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MySubscriptionPlanListAPIView(ListAPIView):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = MySubscriptionPlanListSerializer
    permission_classes = [IsCreator, ]
    filter_backends = [OrderingFilter, ]
    ordering_fields = ['price']
    ordering = ['-price']

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        queryset = queryset.filter(creator=user)
        return queryset


class AddSubscriptionPlanAPIView(CreateAPIView):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = AddSubscriptionPlanSerializer
    permission_classes = [IsCreator, ]


class MySubscriptionPlanRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = MySubscriptionPlanRetrieveUpdateSerializer
    permission_classes = [IsCreator, ]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        queryset = queryset.filter(creator=user)
        return queryset


class LikedPostListAPIView(ListAPIView):
    serializer_class = PostListSerializer
    pagination_class = APILimitOffsetPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        queryset = Post.objects.all()
        queryset = queryset.filter(likes__user=user)
        return queryset


class SavedPostListAPIView(ListAPIView):
    serializer_class = PostListSerializer
    pagination_class = APILimitOffsetPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        queryset = Post.objects.all()
        queryset = queryset.filter(saved_by_users__user=user)
        return queryset


class FundraisingListCreateAPIView(ListCreateAPIView):
    queryset = Fundraising.objects.all()
    serializer_class = FundraisingSerializer
    permission_classes = [IsCreator, ]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        queryset = queryset.filter(creator=user)
        return queryset


class FundraisingDeleteRetrieveUpdateAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Fundraising.objects.all()
    serializer_class = FundraisingSerializer
    permission_classes = [IsCreator, ]


class FollowersDashboardAPIView(APIView):
    permission_classes = [IsCreator, ]

    @swagger_auto_schema(
        operation_description='Period Type',
        manual_parameters=[
            openapi.Parameter(
                'period', in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description=_('Тип для дашборда'),
                enum=['week', 'month']
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        period = request.query_params.get('period', 'week')
        today = localtime(now()).date()

        if period == 'month':
            start_date = today - timedelta(days=30)
            queryset = UserFollow.objects.filter(created_at__date__gte=start_date)

            # Define cutoff days (end of each 5-day chunk)
            checkpoints = [start_date + timedelta(days=i * 5) for i in range(7)]
            checkpoints.append(today)

            result = OrderedDict()

            for i in range(len(checkpoints) - 1):
                start = checkpoints[i]
                end = checkpoints[i + 1]
                count = queryset.filter(
                    created_at__date__gte=start,
                    created_at__date__lte=end
                ).count()

                label = end.strftime('%d %b')
                result[label] = count

            return Response({
                "period": "last_month",
                "interval_follow_counts": result
            })

        elif period == 'week':
            start_date = today - timedelta(days=6)
            queryset = UserFollow.objects.filter(created_at__date__gte=start_date)

            data = queryset.annotate(day=TruncDate('created_at')) \
                .values('day') \
                .annotate(count=Count('id')) \
                .order_by('day')

            days = [(start_date + timedelta(days=i)) for i in range(7)]
            result = {day.strftime('%Y-%m-%d'): 0 for day in days}

            for item in data:
                result[item['day'].strftime('%Y-%m-%d')] = item['count']

            return Response({
                "period": "last_week",
                "daily_follow_counts": result
            })

        return Response({"error": "Invalid period"}, status=400)


class FollowersDashboardByPlanAPIView(APIView):
    permission_classes = [IsCreator, ]

    @swagger_auto_schema(
        operation_description="Get subscriber counts and percentages per subscription plan for the creator.",
        responses={200: FollowersDashboardByPlanSerializer(many=True)}
    )
    def get(self, request):
        creator = request.user  # Assuming the authenticated user is the creator

        # Annotate each plan with subscriber count
        plans = SubscriptionPlan.objects.filter(creator=creator).annotate(
            subscriber_count=Count(
                'usersubscription',
                filter=Q(usersubscription__is_active=True)
            )
        )

        # Compute total subscriber count across all plans
        total_subscribers = sum(plan.subscriber_count for plan in plans)

        # Avoid division by zero
        response_data = []
        for plan in plans:
            percent = (
                (plan.subscriber_count / total_subscribers * 100)
                if total_subscribers > 0 else 0
            )
            response_data.append({
                'id': plan.id,
                'name': plan.name,
                'subscriber_count': plan.subscriber_count,
                'percent': round(percent, 2),  # Rounded to 2 decimal places
            })

        return Response(response_data)
