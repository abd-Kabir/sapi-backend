from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _

from apps.content.models import Post, Category, PostTypes, ReportTypes
from apps.content.serializers import PostCreateSerializer, CategorySerializer, ChoiceTypeSerializer, \
    PostAccessibilitySerializer, QuestionnairePostAnswerSerializer
from config.core.api_exceptions import APIValidation
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
