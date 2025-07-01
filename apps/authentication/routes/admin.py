from datetime import timedelta

from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.filters import ReportFilter, NotifDisFilter
from apps.authentication.models import User, PermissionTypes, NotificationDistribution
from apps.authentication.routes.filters import AdminCreatorFilter
from apps.authentication.serializers.admin import AdminCreatorListSerializer, AdminCreatorUpdateSAPIShareSerializer, \
    AdminCreatorRetrieveSerializer, AdminBlockCreatorPostSerializer, ReportListSerializer, ReportRetrieveSerializer, \
    AdminNotifDisSerializer
from apps.authentication.services import creator_earnings, registered_accounts, active_subscriptions, \
    content_type_counts, platform_earnings
from apps.content.models import Report, ReportStatusTypes, ReportComment
from apps.content.serializers import ReportCommentSerializer, AdminUserModifySerializer, AdminUserListSerializer
from config.core.api_exceptions import APIValidation
from config.core.pagination import APILimitOffsetPagination
from config.core.permissions import IsAdmin
from config.swagger import report_status_swagger_param, report_type_swagger_param, date_from_swagger_param, \
    date_to_swagger_param, admin_creator_list_params, period_swagger_param, start_date_swagger_param, \
    end_date_swagger_param, dashboard_user_type_swagger_param, notif_dis_status_swagger_param, \
    notif_dis_type_swagger_param, dashboard_type_swagger_param


class DashboardCreatorEarningsAPIView(APIView):
    permission_classes = [IsAdmin, ]
    router_name = 'STATISTICS'

    @staticmethod
    def get_action():
        return 'list'

    @swagger_auto_schema(manual_parameters=[period_swagger_param, start_date_swagger_param, end_date_swagger_param,
                                            dashboard_user_type_swagger_param, dashboard_type_swagger_param],
                         responses={
                             200: openapi.Response(
                                 description='Analytics data retrieved successfully',
                                 examples={
                                     'application/json': {
                                         'creator_earnings': {'data': 35200},
                                         'registered_accounts': {
                                             'data': [
                                                 {
                                                     'date': '2025-05-31',
                                                     'count': 4
                                                 },
                                                 {
                                                     'date': '2025-06-04',
                                                     'count': 1
                                                 },
                                                 {
                                                     'date': '2025-06-06',
                                                     'count': 1
                                                 },
                                                 {
                                                     'date': '2025-06-26',
                                                     'count': 1
                                                 },
                                                 {
                                                     'date': '2025-06-27',
                                                     'count': 1
                                                 }
                                             ]
                                         },
                                         'active_accounts': {
                                             'data': [
                                                 {
                                                     'date': '2025-05-31',
                                                     'count': 4
                                                 },
                                                 {
                                                     'date': '2025-06-06',
                                                     'count': 1
                                                 },
                                                 {
                                                     'date': '2025-06-26',
                                                     'count': 1
                                                 },
                                                 {
                                                     'date': '2025-06-27',
                                                     'count': 1
                                                 }
                                             ]
                                         },
                                         'new_registered_accounts': {
                                             'data': [
                                                 {
                                                     'date': '2025-06-26',
                                                     'count': 1
                                                 },
                                                 {
                                                     'date': '2025-06-27',
                                                     'count': 1
                                                 }
                                             ]
                                         },
                                         'active_subscriptions': {
                                             'data': [
                                                 {
                                                     'date': '2025-06-27',
                                                     'count': 1
                                                 }
                                             ]
                                         },
                                         'content_type_counts': {
                                             'data': [
                                                 {
                                                     'type': 'Музыка',
                                                     'count': 1
                                                 }
                                             ]
                                         },
                                         'platform_earnings': {
                                             'total_amount': 4800,
                                             'data': [
                                                 {
                                                     'date': '2025-06-11',
                                                     'amount': 3600
                                                 },
                                                 {
                                                     'date': '2025-06-12',
                                                     'amount': 1200
                                                 }
                                             ]
                                         }
                                     }
                                 })
                         })
    def get(self, request, *args, **kwargs):
        period = request.query_params.get('period', 'day')
        trunc_func = {  # TODO: not understood, end it later
            'day': TruncDate,
            'week': TruncWeek,
            'month': TruncMonth
        }.get(period, TruncDate)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        user_type = request.query_params.get('user_type')
        dashboard_type = request.query_params.get('dashboard_type')

        new_reg_start_date = (now() - timedelta(days=7)).strftime('%Y-%m-%d')
        new_reg_end_date = now().strftime('%Y-%m-%d')

        dashboard_funcs = {
            'creator_earnings': lambda: creator_earnings(),
            'registered_accounts': lambda: registered_accounts(trunc_func, user_type, start_date, end_date, None),
            'active_accounts': lambda: registered_accounts(trunc_func, user_type, start_date, end_date, True),
            'new_registered_accounts': lambda: registered_accounts(trunc_func, user_type, new_reg_start_date,
                                                                   new_reg_end_date, None),
            'active_subscriptions': lambda: active_subscriptions(trunc_func, start_date, end_date),
            'content_type_counts': lambda: content_type_counts(),
            'platform_earnings': lambda: platform_earnings(trunc_func, start_date, end_date),
        }
        if dashboard_type not in dashboard_funcs:
            raise APIValidation(_('Invalid dashboard_type'), status_code=status.HTTP_400_BAD_REQUEST)

        response = dashboard_funcs[dashboard_type]()
        return Response(response)


class AdminCreatorListAPIView(ListAPIView):
    queryset = User.all_objects.filter(is_admin=False).order_by('-date_joined')
    serializer_class = AdminCreatorListSerializer
    permission_classes = [IsAdmin, ]
    pagination_class = APILimitOffsetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = AdminCreatorFilter
    router_name = 'CREATORS'

    @staticmethod
    def get_action():
        return 'list'

    @swagger_auto_schema(manual_parameters=admin_creator_list_params)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminCreatorRetrieveAPIView(RetrieveAPIView):
    queryset = User.all_objects.filter(is_admin=False).all()
    serializer_class = AdminCreatorRetrieveSerializer
    permission_classes = [IsAdmin, ]
    router_name = 'CREATORS'

    @staticmethod
    def get_action():
        return 'retrieve'


class AdminBlockCreatorPostAPIView(APIView):
    serializer_class = AdminBlockCreatorPostSerializer
    permission_classes = [IsAdmin, ]
    router_name = 'CREATORS_REPORTS'

    @staticmethod
    def get_action():
        return 'update'

    @staticmethod
    def get_creator(pk):
        try:
            return User.all_objects.get(pk=pk)
        except:
            raise APIValidation(_('Контент креатор не найден'), status_code=404)

    @swagger_auto_schema(request_body=AdminBlockCreatorPostSerializer,
                         responses={200: AdminCreatorRetrieveSerializer()})
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = self.get_creator(data.get('user_id'))
        user.is_blocked_by = request.user
        user.block_desc = data.get('block_desc')
        user.block_reason = data.get('block_reason')
        user.temp_phone_number = user.phone_number
        user.phone_number = None
        user.temp_username = user.username
        user.username = None
        user.save(update_fields=['is_blocked_by', 'block_desc', 'block_reason', 'temp_phone_number', 'phone_number',
                                 'temp_username', 'username'])

        return Response(status=status.HTTP_200_OK)


class AdminCreatorSAPIShareAPIView(APIView):
    response_serializer_class = AdminCreatorRetrieveSerializer
    serializer_class = AdminCreatorUpdateSAPIShareSerializer
    permission_classes = [IsAdmin, ]
    router_name = 'CREATORS'

    @staticmethod
    def get_action():
        return 'update'

    @staticmethod
    def get_creator(pk):
        try:
            return User.all_objects.get(pk=pk)
        except:
            raise APIValidation(_('Контент креатор не найден'), status_code=404)

    @swagger_auto_schema(request_body=AdminCreatorUpdateSAPIShareSerializer,
                         responses={200: AdminCreatorRetrieveSerializer()})
    def patch(self, request, pk, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        creator = self.get_creator(pk)

        creator.sapi_share = data.get('sapi_share')
        creator.save(update_fields=['sapi_share'])
        response = self.response_serializer_class(creator).data
        return Response(response)


class AdminIgnoreReportAPIView(APIView):
    permission_classes = [IsAdmin, ]
    router_name = 'REPORTS'

    @staticmethod
    def get_action():
        return 'update'

    @staticmethod
    def get_report(report_id):
        try:
            return Report.objects.get(pk=report_id)
        except:
            raise APIValidation(_('Жалобы не найдено'), status_code=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(responses={200: openapi.Response(description='Successful response.')})
    def post(self, request, report_id):
        report = self.get_report(report_id)
        report.status = ReportStatusTypes.ignored
        report.resolve(request.user)
        return Response(status=status.HTTP_200_OK)


class AdminBlockPostAPIView(APIView):
    permission_classes = [IsAdmin, ]
    router_name = 'REPORTS'

    @staticmethod
    def get_action():
        return 'update'

    @staticmethod
    def get_report(report_id):
        try:
            return Report.objects.get(pk=report_id, status=ReportStatusTypes.waiting)
        except:
            raise APIValidation(_('Жалобы не найдено'), status_code=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(responses={200: openapi.Response(description='Successful response.')})
    def post(self, request, report_id):
        report = self.get_report(report_id)
        report.status = ReportStatusTypes.blocked_post
        report.resolve(request.user)
        post = report.post
        post.is_blocked = True
        post.save(update_fields=['is_blocked'])
        return Response(status=status.HTTP_200_OK)


class AdminReportCommentAPIView(CreateAPIView):
    queryset = ReportComment.objects.all()
    serializer_class = ReportCommentSerializer
    permission_classes = [IsAdmin, ]
    router_name = 'REPORTS'

    @staticmethod
    def get_action():
        return 'create'


class AdminUserPermissionListAPIView(APIView):
    permission_classes = [IsAdmin, ]
    router_name = 'ADMINS'

    @staticmethod
    def get_action():
        return 'list'

    @swagger_auto_schema(operation_description='List of permissions for creating admin user.',
                         responses={200: openapi.Response(
                             description='Successful response.',
                             examples={
                                 'application/json': {
                                     "STATISTICS": {
                                         "name": "Статистика",
                                         "permissions": [
                                             {
                                                 "code": "VIEW_STATISTICS",
                                                 "name": "Просмотр статистики"
                                             },
                                             {
                                                 "code": "MODIFY_STATISTICS",
                                                 "name": "Редактирование статистики"
                                             }
                                         ]
                                     },
                                     "SENDING_NOTIFICATIONS": {
                                         "name": "Рассылка уведомлений",
                                         "permissions": []
                                     },
                                     "REPORTS": {
                                         "name": "Жалобы",
                                         "permissions": [
                                             {
                                                 "code": "VIEW_REPORTS",
                                                 "name": "Просмотр жалоб"
                                             },
                                             {
                                                 "code": "MODIFY_REPORTS",
                                                 "name": "Редактирование жалоб"
                                             }
                                         ]
                                     },
                                     "CREATORS": {
                                         "name": "Креаторы",
                                         "permissions": [
                                             {
                                                 "code": "VIEW_CREATORS",
                                                 "name": "Просмотр креаторов"
                                             },
                                             {
                                                 "code": "MODIFY_CREATORS",
                                                 "name": "Редактирование креаторов"
                                             }
                                         ]
                                     },
                                     "CHATS": {
                                         "name": "Чаты",
                                         "permissions": [
                                             {
                                                 "code": "VIEW_CHATS",
                                                 "name": "Просмотр чата поддержки"
                                             },
                                             {
                                                 "code": "MODIFY_CHATS",
                                                 "name": "Редактирование чата поддержки"
                                             }
                                         ]
                                     },
                                     "ADMINS": {
                                         "name": "Администраторы",
                                         "permissions": [
                                             {
                                                 "code": "VIEW_ADMINS",
                                                 "name": "Просмотр администраторов"
                                             },
                                             {
                                                 "code": "MODIFY_ADMINS",
                                                 "name": "Редактирование администраторов"
                                             }
                                         ]
                                     }

                                 }
                             }
                         )})
    def get(self, request, *args, **kwargs):
        permission_categories = PermissionTypes.categories()
        categories = {}
        for code, name in permission_categories.items():
            categories[code] = {
                'name': name,
                'permissions': []
            }
        for code, name in PermissionTypes.choices:
            category_part = '_'.join(code.split('_')[1:])
            if category_part in categories:
                categories[category_part]['permissions'].append({'code': code, 'name': name})
        return Response(categories)


class AdminUserListAPIView(ListAPIView):
    queryset = User.objects.filter(is_admin=True).order_by('-id')
    serializer_class = AdminUserListSerializer
    permission_classes = [IsAdmin, ]
    router_name = 'ADMINS'
    pagination_class = APILimitOffsetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = [
        'first_name', 'last_name', 'phone_number'
    ]

    @staticmethod
    def get_action():
        return 'list'

    def get_queryset(self):
        return super().get_queryset().exclude(pk=self.request.user.id)


class AdminUserCreationAPIView(APIView):
    serializer_class = AdminUserModifySerializer
    permission_classes = [IsAdmin, ]
    router_name = 'ADMINS'

    @staticmethod
    def get_action():
        return 'create'

    @swagger_auto_schema(request_body=AdminUserModifySerializer(),
                         responses={
                             status.HTTP_200_OK: openapi.Response(
                                 description="Success response",
                                 schema=openapi.Schema(
                                     type=openapi.TYPE_OBJECT,
                                     properties={
                                         'detail': openapi.Schema(type=openapi.TYPE_STRING,
                                                                  description='Information message about creation.'),
                                         'id': openapi.Schema(type=openapi.TYPE_INTEGER,
                                                              description='ID of created admin user.'),
                                     }
                                 ),
                                 examples={
                                     "application/json": {
                                         'detail': 'Админ создан.',
                                         'id': 1
                                     }
                                 }
                             ),
                         })
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin = serializer.save()
        return Response({'detail': _('Админ создан.'), 'id': admin.id}, status=status.HTTP_200_OK)


class AdminUserUpdateAPIView(APIView):
    serializer_class = AdminUserModifySerializer
    permission_classes = [IsAdmin, ]
    router_name = 'ADMINS'

    @staticmethod
    def get_action():
        return 'update'

    @staticmethod
    def get_user(pk):
        try:
            return User.objects.get(pk=pk, is_admin=True)
        except:
            raise APIValidation(_('Пользователь не найден'), status_code=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(request_body=AdminUserModifySerializer(),
                         responses={
                             status.HTTP_200_OK: openapi.Response(
                                 description="Success response",
                                 schema=openapi.Schema(
                                     type=openapi.TYPE_OBJECT,
                                     properties={
                                         'detail': openapi.Schema(type=openapi.TYPE_STRING,
                                                                  description='Information message about update.'),
                                         'id': openapi.Schema(type=openapi.TYPE_INTEGER,
                                                              description='ID of updated admin user.'),
                                     }
                                 ),
                                 examples={
                                     "application/json": {
                                         'detail': 'Изменение применены.',
                                         'id': 1
                                     }
                                 }
                             ),
                         })
    def patch(self, request, pk, *args, **kwargs):
        serializer = self.serializer_class(instance=self.get_user(pk), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        admin = serializer.save()
        return Response({'detail': _('Изменение применены.'), 'id': admin.id}, status=status.HTTP_200_OK)


class AdminUserDeleteAPIView(APIView):
    permission_classes = [IsAdmin, ]
    router_name = 'ADMINS'

    @staticmethod
    def get_action():
        return 'destroy'

    @staticmethod
    def get_user(pk):
        try:
            return User.objects.get(pk=pk, is_admin=True)
        except:
            raise APIValidation(_('Пользователь не найден'), status_code=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description='Just send delete request and admin user will be deleted. Response returns 200.',
    )
    def delete(self, request, pk, *args, **kwargs):
        user = self.get_user(pk)
        user.delete()
        return Response(status=status.HTTP_200_OK)


class ReportListView(ListAPIView):
    queryset = Report.objects.all().order_by('-created_at')
    serializer_class = ReportListSerializer
    permission_classes = [IsAdmin, ]
    pagination_class = APILimitOffsetPagination

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ReportFilter

    search_fields = [
        'post__user__username',
        'user__username',
        'post__title'
    ]
    router_name = 'REPORTS'

    @swagger_auto_schema(
        operation_summary="List reports",
        manual_parameters=[report_type_swagger_param, date_from_swagger_param, date_to_swagger_param,
                           report_status_swagger_param]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @staticmethod
    def get_action():
        return 'list'


class ReportRetrieveAPIView(RetrieveAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportRetrieveSerializer
    permission_classes = [IsAdmin, ]
    router_name = 'REPORTS'

    @staticmethod
    def get_action():
        return 'list'


class AdminNotifDisListAPIView(ListAPIView):
    queryset = NotificationDistribution.objects.all().order_by('-created_at')
    serializer_class = AdminNotifDisSerializer
    pagination_class = APILimitOffsetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = NotifDisFilter
    permission_classes = [IsAdmin, ]
    router_name = 'NOTIFICATIONS'

    search_fields = ['title_uz', 'title_ru', 'text_uz']

    @staticmethod
    def get_action():
        return 'list'

    @swagger_auto_schema(
        operation_summary='List of notifications.',
        manual_parameters=[date_from_swagger_param, date_to_swagger_param, notif_dis_status_swagger_param,
                           notif_dis_type_swagger_param]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminNotifDisCreateAPIView(CreateAPIView):
    queryset = NotificationDistribution.objects.all()
    serializer_class = AdminNotifDisSerializer
    permission_classes = [IsAdmin, ]
    router_name = 'NOTIFICATIONS'

    @staticmethod
    def get_action():
        return 'create'


class AdminNotifDisUpdateAPIView(UpdateAPIView):
    queryset = NotificationDistribution.objects.all()
    serializer_class = AdminNotifDisSerializer
    permission_classes = [IsAdmin, ]
    router_name = 'NOTIFICATIONS'
    http_method_names = ['patch', ]

    @staticmethod
    def get_action():
        return 'update'
