from django.db import IntegrityError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, serializers
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView, UpdateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _

from apps.content.models import Post, Category, PostTypes, ReportTypes, Like, Comment, Report
from apps.content.serializers import PostCreateSerializer, CategorySerializer, ChoiceTypeSerializer, \
    PostAccessibilitySerializer, QuestionnairePostAnswerSerializer, PostListSerializer, \
    PostToggleLikeSerializer, PostShowSerializer, PostShowCommentListSerializer, PostShowCommentRepliesSerializer, \
    PostLeaveCommentSerializer, ReportSerializer
from config.core.api_exceptions import APIValidation
from config.core.pagination import APILimitOffsetPagination
from config.core.permissions import IsCreator, AllowGet, IsAdmin
from config.core.swagger import query_choice_swagger_param
from config.views import BaseModelViewSet


class ChoiceTypeListAPIView(APIView):
    serializer_class = ChoiceTypeSerializer

    def get_queryset(self, choice_type):
        types = {
            'post': PostTypes,
            'report': ReportTypes,
        }
        if not choice_type:
            raise APIValidation(_('Тип параметр не передан'), status_code=status.HTTP_400_BAD_REQUEST)
        queryset = []
        for code, name in types[choice_type].choices:
            queryset.append({'name': name, 'code': code})
        return queryset

    @swagger_auto_schema(
        operation_description='Returns choices for post types or report types',
        manual_parameters=[query_choice_swagger_param],
        responses={200: 'Choice Types'}
    )
    def get(self, request, *args, **kwargs):
        choice_type = request.query_params.get('type')

        queryset = self.get_queryset(choice_type)
        serializer = self.serializer_class(queryset, many=True)
        data = serializer.data
        return Response(data)


class CategoryModelViewSet(BaseModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowGet, ]

    @swagger_auto_schema(
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=['name'], properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING),
            'icon': openapi.Schema(type=openapi.TYPE_INTEGER)
        }),
        responses={status.HTTP_201_CREATED: CategorySerializer()}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, required=['name'], properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING),
            'icon': openapi.Schema(type=openapi.TYPE_INTEGER)
        }),
        responses={status.HTTP_201_CREATED: CategorySerializer()}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class PostCreateAPIView(CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostCreateSerializer
    permission_classes = [IsCreator, ]


class PostAccessibilityAPIView(UpdateAPIView):
    queryset = Post.all_objects.all()
    serializer_class = PostAccessibilitySerializer
    permission_classes = [IsCreator, ]


class QuestionnairePostAnswerAPIView(APIView):
    serializer_class = QuestionnairePostAnswerSerializer

    @swagger_auto_schema(request_body=QuestionnairePostAnswerSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PostByCategoryListAPIView(ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostListSerializer
    pagination_class = APILimitOffsetPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(category_id=self.kwargs['category_id'])
        return queryset


class PostByUserListAPIView(ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostListSerializer
    pagination_class = APILimitOffsetPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user_id=self.kwargs['user_id'])
        return queryset


class PostShowAPIView(RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostShowSerializer


class PostShowCommentListAPIView(ListAPIView):
    queryset = Comment.objects.filter(parent__isnull=True)
    serializer_class = PostShowCommentListSerializer
    pagination_class = APILimitOffsetPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(post_id=self.kwargs['post_id'])
        return queryset


class PostShowRepliesListAPIView(ListAPIView):
    queryset = Comment.objects.all()
    serializer_class = PostShowCommentRepliesSerializer
    pagination_class = APILimitOffsetPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(parent_id=self.kwargs['comment_id'])
        return queryset


class PostToggleLikeAPIView(APIView):
    serializer_class = PostToggleLikeSerializer

    @staticmethod
    def get_post(post_id):
        try:
            return Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise APIValidation(_('Пост не найден'), status_code=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def get_comment(comment_id):
        try:
            return Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            raise APIValidation(_('Комментарий не найден'), status_code=status.HTTP_404_NOT_FOUND)

    def like_comment(self, comment_id):
        request = self.request
        comment = self.get_comment(comment_id)
        user = request.user
        like_obj, created = Like.objects.get_or_create(comment=comment, user=user)
        if created:
            response = {'detail': _('Вы лайкнули этот комментарий')}
        else:
            like_obj.delete()
            response = {'detail': _('Вы убрали лайк с этого комментарийа')}
        comment.update_like_count()
        return response

    def like_post(self, post_id):
        request = self.request
        post = self.get_post(post_id)
        user = request.user
        like_obj, created = Like.objects.get_or_create(post=post, user=user)
        if created:
            response = {'detail': _('Вы лайкнули этот пост')}
        else:
            like_obj.delete()
            response = {'detail': _('Вы убрали лайк с этого поста')}
        post.update_counts()
        return response

    @swagger_auto_schema(request_body=PostToggleLikeSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        post_id = data.get('post_id')
        comment_id = data.get('comment_id')
        if post_id and comment_id:
            raise APIValidation(_('Принимается только пост или комментарий'), status_code=status.HTTP_400_BAD_REQUEST)
        if post_id:
            response = self.like_post(post_id)
        elif comment_id:
            response = self.like_comment(comment_id)
        else:
            raise APIValidation(_('Пост или комментарий не найден'), status_code=status.HTTP_400_BAD_REQUEST)
        return Response(response)


class PostLeaveCommentAPIView(APIView):
    serializer_class = PostLeaveCommentSerializer

    @staticmethod
    def get_post(post_id):
        try:
            return Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise APIValidation(_('Пост не найден'), status_code=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def get_comment(comment_id):
        try:
            return Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            raise APIValidation(_('Комментарий не найден'), status_code=status.HTTP_404_NOT_FOUND)

    def leave_comment(self, post_id, text):
        user = self.request.user

        post = self.get_post(post_id)
        Comment.objects.create(user=user, post=post, text=text)
        return {'detail': _('Вы оставили комментарий')}

    def leave_reply(self, post_id, comment_id, text):
        user = self.request.user

        post = self.get_post(post_id)
        parent = self.get_comment(comment_id)
        Comment.objects.create(user=user, post=post, parent=parent, text=text)
        return {'detail': _('Вы оставили ответ на комментарий')}

    @swagger_auto_schema(request_body=PostLeaveCommentSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        post_id = data.get('post_id')
        comment_id = data.get('comment_id')
        text = data.get('text')
        if comment_id:
            response = self.leave_reply(post_id, comment_id, text)
        elif post_id:
            response = self.leave_comment(post_id, text)
        else:
            raise APIValidation(_('Пост или комментарий не найден'), status_code=status.HTTP_400_BAD_REQUEST)
        post = self.get_post(post_id)
        post.update_counts()
        return Response(response)


class CreateReportAPIView(CreateAPIView):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            raise serializers.ValidationError({"detail": "You have already reported this post."})


class ReportListView(ListAPIView):
    serializer_class = ReportSerializer
    permission_classes = [IsAdmin, ]

    def get_queryset(self):
        # Filter by resolved/unresolved if query param provided
        is_resolved = self.request.query_params.get('is_resolved', None)
        queryset = Report.objects.all()

        if is_resolved is not None:
            queryset = queryset.filter(is_resolved=is_resolved.lower() == 'true')

        return queryset.order_by('-created_at')


class ResolveReportAPIView(APIView):
    permission_classes = [IsAdmin, ]

    def get_report(self, pk):
        try:
            return Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            raise APIValidation(_('Жалоба не найден'), status_code=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk, *args, **kwargs):
        instance = self.get_report(pk)
        if instance.is_resolved:
            return Response(
                {'detail': _('Этот отчёт уже закрыт.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = request.user
        instance.resolve(resolved_by_user=user)

        return Response({'id': instance.id, 'is_resolved': instance.is_resolved})


class PostToggleSaveAPIView(APIView):

    @staticmethod
    def get_post(post_id):
        try:
            return Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise APIValidation(_('Пост не найден'), status_code=status.HTTP_404_NOT_FOUND)

    def post(self, request, post_id, *args, **kwargs):
        post = self.get_post(post_id)
        saved = post.toggle_saving_post(request.user)
        if saved:
            response = {'detail': _('Пост сохранен')}
        else:
            response = {'detail': _('Пост убран из сохраненных')}
        return Response(response)
