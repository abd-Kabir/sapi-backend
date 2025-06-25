from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView, RetrieveAPIView, get_object_or_404, CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import User, PermissionTypes
from apps.authentication.serializers.admin import AdminCreatorListSerializer, AdminCreatorUpdateSAPIShareSerializer, \
    AdminCreatorRetrieveSerializer, AdminBlockCreatorSerializer
from apps.content.models import Report, ReportStatusTypes, Post, ReportComment
from apps.content.serializers import ReportCommentSerializer, AdminUserModifySerializer, AdminUserListSerializer
from config.core.api_exceptions import APIValidation
from config.core.pagination import APILimitOffsetPagination
from config.core.permissions import IsAdmin


class AdminCreatorListAPIView(ListAPIView):
    queryset = User.all_objects.filter(is_admin=False).order_by('-date_joined')
    serializer_class = AdminCreatorListSerializer
    permission_classes = [IsAdmin, ]
    pagination_class = APILimitOffsetPagination
    router_name = 'CREATORS'

    @staticmethod
    def get_action():
        return 'list'


class AdminCreatorRetrieveAPIView(RetrieveAPIView):
    queryset = User.all_objects.filter(is_admin=False).all()
    serializer_class = AdminCreatorRetrieveSerializer
    permission_classes = [IsAdmin, ]
    router_name = 'CREATORS'

    @staticmethod
    def get_action():
        return 'retrieve'


class AdminBlockCreatorAPIView(APIView):
    serializer_class = AdminBlockCreatorSerializer
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

    @swagger_auto_schema(request_body=AdminBlockCreatorSerializer,
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

    @staticmethod
    def get_action():
        return 'list'


class AdminUserCreationAPIView(APIView):
    serializer_class = AdminUserModifySerializer
    permission_classes = [IsAdmin, ]
    router_name = 'ADMINS'

    @staticmethod
    def get_action():
        return 'create'

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

    def delete(self, request, pk, *args, **kwargs):
        user = self.get_user(pk)
        user.delete()
        return Response(status=status.HTTP_200_OK)
