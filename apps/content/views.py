from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import CreateAPIView, UpdateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _

from apps.content.models import Post, Category, PostTypes, ReportTypes, Like
from apps.content.serializers import PostCreateSerializer, CategorySerializer, ChoiceTypeSerializer, \
    PostAccessibilitySerializer, QuestionnairePostAnswerSerializer, PostByCategoryListSerializer, \
    PostToggleLikeSerializer
from config.core.api_exceptions import APIValidation
from config.core.pagination import APILimitOffsetPagination
from config.core.permissions import IsCreator, AllowGet
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
    serializer_class = PostByCategoryListSerializer
    pagination_class = APILimitOffsetPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class PostToggleLikeAPIView(APIView):
    serializer_class = PostToggleLikeSerializer

    @staticmethod
    def get_post(post_id):
        try:
            return Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise APIValidation(_('Пост не найден'), status_code=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(request_body=PostToggleLikeSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        post_id = data.get('post_id')
        post = self.get_post(post_id)
        user = request.user
        like_obj, created = Like.objects.get_or_create(post=post, user=user)
        if created:
            response = {'detail': _('Вы лайкнули этот пост')}
        else:
            like_obj.delete()
            response = {'detail': _('Вы убрали лайк с этого поста')}
        post.update_counts()
        return Response(response)
