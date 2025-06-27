from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import User
from apps.content.models import ReportTypes, Report, ReportComment
from apps.files.serializers import FileSerializer


class AdminCreatorListSerializer(serializers.ModelSerializer):
    subscribers_count = serializers.SerializerMethodField(allow_null=True)
    followers_count = serializers.SerializerMethodField(allow_null=True)
    status = serializers.SerializerMethodField(allow_null=True)
    username = serializers.SerializerMethodField(allow_null=True)
    phone_number = serializers.SerializerMethodField(allow_null=True)

    profile_photo_info = FileSerializer(read_only=True, allow_null=True, source='profile_photo')
    profile_banner_photo_info = FileSerializer(read_only=True, allow_null=True, source='profile_banner_photo')
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)

    @staticmethod
    def get_subscribers_count(obj):
        return obj.subscribers_count()

    @staticmethod
    def get_followers_count(obj):
        return obj.followers_count()

    @staticmethod
    def get_status(obj):
        if obj.is_blocked_by:
            status = _('Заблокирован')
        else:
            status = _('Активен') if obj.is_creator else _('Не активен')
        return status

    @staticmethod
    def get_username(obj):
        return obj.username if obj.username else obj.temp_username

    @staticmethod
    def get_phone_number(obj):
        return obj.phone_number if obj.phone_number else obj.temp_phone_number

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'phone_number',
            'subscribers_count',
            'followers_count',
            'sapi_share',
            'date_joined',
            'status',

            'profile_photo_info',
            'profile_banner_photo_info',
            'category_name',
        ]


class AdminCreatorRetrieveSerializer(serializers.ModelSerializer):
    subscribers_count = serializers.SerializerMethodField(allow_null=True)
    followers_count = serializers.SerializerMethodField(allow_null=True)
    status = serializers.SerializerMethodField(allow_null=True)

    profile_photo_info = FileSerializer(read_only=True, allow_null=True, source='profile_photo')
    profile_banner_photo_info = FileSerializer(read_only=True, allow_null=True, source='profile_banner_photo')
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)

    @staticmethod
    def get_subscribers_count(obj):
        return obj.subscribers_count()

    @staticmethod
    def get_followers_count(obj):
        return obj.followers_count()

    @staticmethod
    def get_status(obj):
        if obj.is_blocked_by:
            status = _('Заблокирован')
        else:
            status = _('Активен') if obj.is_creator else _('Не активен')
        return status

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'phone_number',
            'subscribers_count',
            'followers_count',
            'sapi_share',
            'date_joined',
            'status',

            'profile_photo_info',
            'profile_banner_photo_info',
            'category_name',
        ]


class AdminBlockCreatorSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    block_reason = serializers.ChoiceField(choices=ReportTypes.choices)
    block_desc = serializers.CharField(required=False)


class AdminCreatorUpdateSAPIShareSerializer(serializers.Serializer):
    sapi_share = serializers.IntegerField()


class ReportListSerializer(serializers.ModelSerializer):
    post_username = serializers.CharField(source='post.user.username', read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)
    post_description = serializers.CharField(source='post.description', read_only=True)
    reported_username = serializers.CharField(source='user.username', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Report
        fields = [
            'id',
            'post',
            'post_username',
            'post_title',
            'post_description',
            'report_type',
            'description',
            'is_resolved',
            'resolved_at',
            'resolved_by',
            'status_display',
            'reported_username',
            'report_type_display',
            'created_at',
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


class ReportRetrieveSerializer(serializers.ModelSerializer):
    creator = serializers.SerializerMethodField()
    post_uploaded_at = serializers.DateTimeField(source='post.created_at', read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)
    post_description = serializers.CharField(source='post.description', read_only=True)
    post_files = FileSerializer(source='post.files', many=True, read_only=True)

    reporter = serializers.SerializerMethodField()
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    report_description = serializers.CharField(source='description', read_only=True)
    report_created_at = serializers.DateTimeField(source='created_at', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    admin_comments = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'creator',
            'post_uploaded_at',
            'post_title',
            'post_description',
            'post_files',

            'reporter',
            'report_type',
            'report_type_display',
            'report_description',
            'report_created_at',
            'status',
            'status_display',

            'admin_comments',
        ]

    def get_creator(self, obj):
        user = obj.post.user
        return {
            "id": user.id,
            "username": user.username,
            "profile_photo": FileSerializer(user.profile_photo).data if user.profile_photo else None
        }

    def get_reporter(self, obj):
        user = obj.user
        return {
            "id": user.id,
            "username": user.username,
            "profile_photo": FileSerializer(user.profile_photo).data if user.profile_photo else None
        }

    def get_admin_comments(self, obj):
        comments = ReportComment.objects.filter(report=obj.post).order_by('created_at')
        return [
            {
                "username": c.user.username,
                "text": c.text,
                "created_at": c.created_at.strftime('%d %B, %Y')
            }
            for c in comments
        ]
