from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.authentication.models import User
from apps.content.models import ReportTypes
from apps.files.serializers import FileSerializer


class AdminCreatorListSerializer(serializers.ModelSerializer):
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
        if obj.is_blocked_by_admin:
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
        if obj.is_blocked_by_admin:
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


class AdminCreatorUpdateSAPIShareSerializer(serializers.Serializer):
    sapi_share = serializers.IntegerField()
