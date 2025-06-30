from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status

from apps.authentication.models import User, UserPermissions, PermissionTypes
from apps.authentication.serializers.user import BecomeCreatorSerializer
from apps.content.models import Post, Category, AnswerOption, PostAnswer, Comment, Report, ReportComment
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
            'files',
            'answers',
            'allow_multiple_answers',
        ]


class PostAccessibilitySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    subscription_name = serializers.CharField(source='subscription.name', read_only=True, allow_null=True)

    def validate(self, attrs):
        user = self.context['request'].user
        post = self.instance
        if post.user != user:
            raise APIValidation(_('У вас недостаточно прав для выполнения данного действия.'),
                                status_code=status.HTTP_403_FORBIDDEN)
        return super().validate(attrs)

    def update(self, instance, validated_data):
        subscription = validated_data.get('subscription')
        instance: Post = super().update(instance, validated_data)
        if subscription:
            instance.is_premium = True
        instance.is_posted = True
        instance.save()
        return instance

    class Meta:
        model = Post
        fields = [
            'id',
            'category',
            'category_name',
            'subscription',
            'subscription_name',
            'publication_time',
        ]


class QuestionnairePostAnswerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)
    answers = serializers.PrimaryKeyRelatedField(many=True, queryset=AnswerOption.objects.all(), required=True)

    class Meta:
        model = Post
        fields = [
            'id',
            'answers'
        ]

    @staticmethod
    def validate_post(pk, answers):
        try:
            post = Post.objects.get(pk=pk, post_type='questionnaire')
            if not post.allow_multiple_answers and len(answers) > 1:
                raise APIValidation(_('Дайте один ответ'), status_code=status.HTTP_400_BAD_REQUEST)
        except Post.DoesNotExist:
            raise APIValidation(_('Опросник не найден'), status_code=status.HTTP_404_NOT_FOUND)

    def validate_answers(self, answers):
        post_id = self.initial_data.get('id')
        if not post_id:
            raise serializers.ValidationError(_('ID поста обязателен для заполнения'))
        self.validate_post(post_id, answers)

        invalid_options = [opt.id for opt in answers if opt.questionnaire_post_id != post_id]
        if invalid_options:
            raise serializers.ValidationError(
                _(f'Варианты ответов {invalid_options} не принадлежат посту {post_id}')
            )

        return answers

    def create(self, validated_data):
        request = self.context.get('request')
        post_id = validated_data['id']
        answer_options = validated_data['answers']

        post_answer, created = PostAnswer.objects.update_or_create(
            user=request.user,
            post_id=post_id,
            defaults={
                'answers': [opt.id for opt in answer_options]
            }
        )

        return post_answer.post

    def to_representation(self, instance):
        request = self.context.get('request')
        representation = super().to_representation(instance)
        representation['answers'] = (
            instance.post_answers
            .filter(user=request.user)
            .first()
            .answers
        )
        return representation


class PostListSerializer(serializers.ModelSerializer):
    user = BecomeCreatorSerializer(allow_null=True, read_only=True)
    post_type_display = serializers.CharField(source='get_post_type_display', read_only=True)
    files = FileSerializer(read_only=True, allow_null=True, many=True)
    has_liked = serializers.SerializerMethodField()
    can_view = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    def get_has_liked(self, obj):
        user = self.context.get('request').user
        return obj.has_liked(user)

    def get_can_view(self, obj):
        user = self.context['request'].user if self.context['request'].user.is_authenticated else None
        return obj.can_view(user)

    def get_is_saved(self, obj: Post):
        user = self.context.get('request').user
        return obj.is_saved_by(user)

    def to_representation(self, instance: Post):
        user = self.context.get('request').user
        representation = super().to_representation(instance)
        if not instance.can_view(user):
            return {
                'id': instance.id,
                'title': instance.title,
                'description': instance.description,
                'like_count': instance.like_count,
                'comment_count': instance.comment_count,
                'post_type': instance.post_type,
                'post_type_display': instance.get_post_type_display(),
                'created_at': instance.created_at,
                'can_view': False,
                'is_saved': instance.is_saved_by(user),
                'user': BecomeCreatorSerializer(instance.user).data
            }
        return representation

    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'description',
            'like_count',
            'comment_count',
            'post_type',
            'post_type_display',
            'created_at',
            'has_liked',
            'can_view',
            'is_saved',
            'files',
            'user',
        ]


class PostShowSerializer(serializers.ModelSerializer):
    post_type_display = serializers.CharField(source='get_post_type_display', read_only=True)
    files = FileSerializer(read_only=True, allow_null=True, many=True)
    has_liked = serializers.SerializerMethodField()

    def get_has_liked(self, obj):
        user = self.context.get('request').user
        return obj.has_liked(user)

    def to_representation(self, instance: Post):
        user = self.context.get('request').user
        representation = super().to_representation(instance)
        if not instance.can_view(user):
            return {
                'id': instance.id,
                'title': instance.title,
                'description': instance.description,
                'like_count': instance.like_count,
                'comment_count': instance.comment_count,
                'post_type': instance.post_type,
                'post_type_display': instance.get_post_type_display(),
                'created_at': instance.created_at
            }
        return representation

    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'description',
            'like_count',
            'comment_count',
            'post_type',
            'post_type_display',
            'created_at',
            'has_liked',
            'files',
        ]


class PostShowCommentListSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()

    def get_has_liked(self, obj):
        user = self.context.get('request').user
        return obj.has_liked(user)

    def get_replies(self, obj):
        replies = obj.replies.all().order_by('-created_at')[:1]
        serializer = PostShowCommentListSerializer(replies, many=True, context=self.context)
        return serializer.data

    class Meta:
        model = Comment
        fields = [
            'id',
            'text',
            'like_count',
            'has_liked',
            'replies',
            'created_at',
        ]


class PostShowCommentRepliesSerializer(serializers.ModelSerializer):
    has_liked = serializers.SerializerMethodField()

    def get_has_liked(self, obj):
        user = self.context.get('request').user
        return obj.has_liked(user)

    class Meta:
        model = Comment
        fields = [
            'id',
            'text',
            'like_count',
            'has_liked',
            'created_at',
        ]


class PostToggleLikeSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(required=False)
    comment_id = serializers.IntegerField(required=False)


class PostLeaveCommentSerializer(serializers.Serializer):
    text = serializers.CharField(required=True)
    post_id = serializers.IntegerField(required=True)
    comment_id = serializers.IntegerField(required=False)


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            'id',
            'post',
            'report_type',
            'description',
            'is_resolved',
            'resolved_at',
            'resolved_by'
        ]
        read_only_fields = [
            'id',
            'is_resolved',
            'resolved_at',
            'resolved_by',
            'user'
        ]

    def create(self, validated_data):
        # Automatically set the user from the request
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ReportCommentSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def create(self, validated_data):
        report_id = self.context['kwargs'].get('report_id')
        comment = ReportComment.objects.create(**validated_data, report_id=report_id)
        return comment

    class Meta:
        model = ReportComment
        fields = [
            'id',
            'user',
            'text',
        ]


class AdminUserListSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'phone_number',
            'permissions',
        ]

    @staticmethod
    def get_permissions(obj):
        return list(obj.permissions.values_list('permission', flat=True))


class AdminUserModifySerializer(serializers.ModelSerializer):
    permissions = serializers.ListField(
        child=serializers.ChoiceField(choices=PermissionTypes.choices),
        write_only=True
    )
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'phone_number',
            'password',
            'permissions',
        ]

    def create(self, validated_data):
        with transaction.atomic():
            permissions = validated_data.pop('permissions')
            password = validated_data.pop('password')
            user = User.objects.create_user(**validated_data, password=password, is_admin=True)

            UserPermissions.objects.bulk_create([
                UserPermissions(user=user, permission=perm)
                for perm in permissions
            ])
            return user

    def update(self, instance: User, validated_data):
        with transaction.atomic():
            permissions = validated_data.pop('permissions', None)
            password = validated_data.pop('password', None)
            for key, value in validated_data.items():
                setattr(instance, key, value)
            if password:
                instance.set_password(password)
            if permissions:
                instance.permissions.all().delete()
                UserPermissions.objects.bulk_create([
                    UserPermissions(user=instance, permission=perm)
                    for perm in permissions
                ])
            instance.save()
            return instance
