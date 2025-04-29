from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status

from apps.content.models import Post, Category, AnswerOption
from apps.files.models import File
from apps.files.serializers import FileSerializer
from config.core.api_exceptions import APIValidation


class ChoiceTypeSerializer(serializers.Serializer):
    name = serializers.CharField()
    code = serializers.CharField()


class CategorySerializer(serializers.ModelSerializer):
    icon_info = FileSerializer(read_only=True, allow_null=True, source='icon')

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'icon',
            'icon_info',
        ]


class AnswerOptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = [
            'text',
            'is_correct',
        ]


class PostCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    answers = AnswerOptionCreateSerializer(required=False, many=True)
    files = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=File.objects.all(),
        required=False
    )

    def validate(self, attrs):
        post_type = attrs.get('post_type')
        if post_type == 'questionnaire' and not attrs.get('answers'):
            raise APIValidation(_('В опроснике не отправлены ответы.'), status_code=status.HTTP_400_BAD_REQUEST)
        # if post_type == 'questionnaire':
        #     allow_multiple_answers = attrs.get('allow_multiple_answers')
        #     correct_answers_count = len([i.get('is_correct') for i in attrs.get('answers') if i.get('is_correct')])
        #     if allow_multiple_answers and not correct_answers_count > 1:
        #         raise APIValidation(_('Выбрано мульти-ответ, но отправлено только один ответ.'),
        #                             status_code=status.HTTP_400_BAD_REQUEST)
        return super().validate(attrs)

    def create(self, validated_data):
        with transaction.atomic():
            files = validated_data.pop('files', [])
            answers = validated_data.pop('answers', [])
            post = Post.objects.create(**validated_data)
            if files:
                post.files.add(*files)
            if answers and validated_data.get('post_type') == 'questionnaire':
                answers_list = []
                for answer in answers:
                    answers_list.append(AnswerOption(questionnaire_post=post, **answer))
                AnswerOption.objects.bulk_create(answers_list)
            return post

    class Meta:
        model = Post
        fields = [
            'id',
            'user',
            'title',
            'description',
            'post_type',
            'category',
            'files',
            'answers',
            'allow_multiple_answers',
        ]
