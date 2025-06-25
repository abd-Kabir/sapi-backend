from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView, RetrieveAPIView, get_object_or_404, CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import User
from apps.authentication.serializers.admin import AdminCreatorListSerializer, AdminCreatorUpdateSAPIShareSerializer, \
    AdminCreatorRetrieveSerializer, AdminBlockCreatorSerializer
from apps.content.models import Report, ReportStatusTypes, Post, ReportComment
from apps.content.serializers import ReportCommentSerializer
from config.core.api_exceptions import APIValidation
from config.core.pagination import APILimitOffsetPagination
from config.core.permissions import IsAdmin


class AdminCreatorListAPIView(ListAPIView):
    queryset = User.all_objects.all()
    serializer_class = AdminCreatorListSerializer
    permission_classes = [IsAdmin, ]
    pagination_class = APILimitOffsetPagination


class AdminCreatorRetrieveAPIView(RetrieveAPIView):
    queryset = User.all_objects.all()
    serializer_class = AdminCreatorRetrieveSerializer
    permission_classes = [IsAdmin, ]


class AdminBlockCreatorAPIView(APIView):
    serializer_class = AdminBlockCreatorSerializer
    permission_classes = [IsAdmin, ]

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
        user.block_reason = data.get('block_reason')
        user.save(update_fields=['is_blocked_by'])

        return Response(status=status.HTTP_200_OK)


class AdminCreatorSAPIShareAPIView(APIView):
    response_serializer_class = AdminCreatorRetrieveSerializer
    serializer_class = AdminCreatorUpdateSAPIShareSerializer
    permission_classes = [IsAdmin, ]

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

    @swagger_auto_schema(responses={200: openapi.Response(description='Successful response.')})
    def post(self, request, post_id):
        unresolved_reports = Report.objects.filter(post_id=post_id, is_resolved=False)

        if not unresolved_reports.exists():
            return Response({'detail': _('Для этого поста не было найдена жалоб.')},
                            status=status.HTTP_404_NOT_FOUND)

        for report in unresolved_reports:
            report.status = ReportStatusTypes.ignored
            report.resolve(request.user)

        return Response(status=status.HTTP_200_OK)


class AdminBlockPostAPIView(APIView):
    permission_classes = [IsAdmin, ]

    @staticmethod
    def resolve_reports(post_id, user):
        unresolved_reports = Report.objects.filter(post_id=post_id, is_resolved=False)
        for report in unresolved_reports:
            report.status = ReportStatusTypes.blocked_post
            report.resolve(user)
    @swagger_auto_schema(responses={200:openapi.Response(description='Successful response.')})
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        if post.is_blocked:
            self.resolve_reports(post_id, request.user)
            return Response({'detail': _('Пост уже заблокирован.')},
                            status=status.HTTP_400_BAD_REQUEST)
        post.is_blocked = True
        post.save(update_fields=['is_blocked'])
        self.resolve_reports(post_id, request.user)
        return Response(status=status.HTTP_200_OK)


class AdminReportCommentAPIView(CreateAPIView):
    queryset = ReportComment.objects.all()
    serializer_class = ReportCommentSerializer
    permission_classes = [IsAdmin, ]

