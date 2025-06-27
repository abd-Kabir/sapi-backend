from django.db import IntegrityError
from django.db.models import Q, OuterRef, Exists
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, serializers
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView, UpdateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import UserFollow, UserSubscription, User
from apps.authentication.services import create_activity
from apps.content.filters import PostByUserFilter
from apps.content.models import Post, Category, PostTypes, ReportTypes, Like, Comment, Report
from apps.content.serializers import PostCreateSerializer, CategorySerializer, ChoiceTypeSerializer, \
    PostAccessibilitySerializer, QuestionnairePostAnswerSerializer, PostListSerializer, \
    PostToggleLikeSerializer, PostShowSerializer, PostShowCommentListSerializer, PostShowCommentRepliesSerializer, \
    PostLeaveCommentSerializer, ReportSerializer
from config.core.api_exceptions import APIValidation
from config.core.pagination import APILimitOffsetPagination
from config.core.permissions import IsCreator, IsAdmin, IsAdminAllowGet
from config.swagger import query_choice_swagger_param, post_type_swagger_param
from config.services import run_with_thread
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
    permission_classes = [IsAdminAllowGet, ]

    def get_action(self):
        return self.action

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
    serializer_class = PostCreateSerializer
    permission_classes = [IsCreator, ]

    def get_queryset(self):
        return Post.objects.all()


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
    serializer_class = PostListSerializer
    pagination_class = APILimitOffsetPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Post.objects.all()
        queryset = queryset.filter(category_id=self.kwargs['category_id'])
        return queryset


class PostByUserListAPIView(ListAPIView):
    serializer_class = PostListSerializer
    pagination_class = APILimitOffsetPagination
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    filterset_class = PostByUserFilter
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    @swagger_auto_schema(manual_parameters=[post_type_swagger_param])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Post.objects.all()
        queryset = queryset.filter(user_id=self.kwargs['user_id'])
        return queryset


class PostByFollowedListAPIView(ListAPIView):
    serializer_class = PostListSerializer
    pagination_class = APILimitOffsetPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user

        followed = UserFollow.objects.filter(
            follower=user,
            followed_id=OuterRef('user_id')
        )
        subscribed = UserSubscription.objects.filter(
            subscriber=user,
            creator_id=OuterRef('user_id'),
            is_active=True
        )

        queryset = Post.objects.all()
        queryset = (
            queryset
            .annotate(is_followed=Exists(followed), is_subscribed=Exists(subscribed))
            .filter(Q(is_followed=True) | Q(is_subscribed=True), is_deleted=False)
        )
        return queryset


class PostShowAPIView(RetrieveAPIView):
    serializer_class = PostShowSerializer

    def get_queryset(self):
        return Post.objects.all()


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
        if user != comment.user:
            run_with_thread(create_activity, ('liked_comment', None,
                                              like_obj.id if created else None, user, comment.user))
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
        if user != post.user:
            run_with_thread(create_activity, ('liked_post', None,
                                              like_obj.id if created else None, user, post.user))
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
        comment = Comment.objects.create(user=user, post=post, text=text)
        if user != post.user:
            run_with_thread(create_activity, ('commented', None, comment.id, user, post.user))
        return {'detail': _('Вы оставили комментарий')}

    def leave_reply(self, post_id, comment_id, text):
        user = self.request.user

        post = self.get_post(post_id)
        parent = self.get_comment(comment_id)
        comment = Comment.objects.create(user=user, post=post, parent=parent, text=text)
        if user != post.user:
            run_with_thread(create_activity, ('replied', None, comment.id, user, post.user))
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
            raise serializers.ValidationError({'detail': _('Вы уже пожаловались на этот пост.')})


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


class PopularCreatorListAPIView(APIView):

    def most_popular_creators(self, limit: int = 10):
        return

    def popular_creators_by_category(self, limit_per_category: int = 5):
        """
        Returns popular creators grouped by category
        :param limit_per_category: Number of creators to return per category
        :return: Dictionary with categories as keys and lists of creators as values
        """
        from collections import defaultdict
        from django.db.models import Count

        # Get all categories that have creators
        categories_with_creators = Category.objects.filter(
            users__is_creator=True,
            users__is_deleted=False
        ).distinct()

        result = defaultdict(list)

        for category in categories_with_creators:
            creators = User.objects.filter(
                category=category,
                is_creator=True,
                is_deleted=False
            ).annotate(
                follower_count=Count('followers')
            ).order_by('-follower_count')[:limit_per_category]

            if creators:
                result[category] = creators

        return dict(result)

    def get(self, request, *args, **kwargs):

        return Response()
