from django.db.models import Q
from django.utils.timezone import now
from rest_framework import serializers

from apps.authentication.models import User
from apps.files.serializers import FileSerializer
from apps.integrations.services.sms_services import only_phone_numbers, verify_sms_code


class BecomeCreatorSerializer(serializers.ModelSerializer):
    profile_photo_info = FileSerializer(read_only=True, allow_null=True, source='profile_photo')
    profile_banner_photo_info = FileSerializer(read_only=True, allow_null=True, source='profile_banner_photo')
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id',
            'category',
            'category_name',
            'username',
            'creator_description',
            'profile_photo',
            'profile_photo_info',
            'profile_banner_photo',
            'profile_banner_photo_info',
        ]


class DeleteAccountVerifySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6, required=True)

    def validate(self, attrs):
        user = self.context['request'].user
        sms = attrs.get('code')
        verify_sms_code(user, sms)
        return super().validate(attrs)


class UserRetrieveSerializer(serializers.ModelSerializer):
    profile_photo_info = FileSerializer(read_only=True, allow_null=True, source='profile_photo')
    profile_banner_photo_info = FileSerializer(read_only=True, allow_null=True, source='profile_banner_photo')
    posts_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    subscribers_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    is_followed_by_you = serializers.SerializerMethodField()
    has_subscription = serializers.SerializerMethodField()

    @staticmethod
    def get_posts_count(obj: User):
        return obj.posts.filter((Q(publication_time__lte=now()) | Q(publication_time=None)), is_posted=True).count()

    @staticmethod
    def get_followers_count(obj):
        # user = self.context['request'].user
        return obj.followers_count()

    @staticmethod
    def get_subscribers_count(obj):
        # user = self.context['request'].user
        return 0

    def get_is_following(self, obj):
        user = self.context['request'].user
        return obj.is_following(user)

    def get_is_followed_by_you(self, obj):
        user = self.context['request'].user
        return obj.is_followed_by(user)

    @staticmethod
    def get_has_subscription(obj):
        # TODO: end subscription creation and subs logic
        # user = self.context['request'].user
        return False

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'profile_photo_info',
            'profile_banner_photo_info',
            'posts_count',
            'followers_count',
            'subscribers_count',
            'is_following',
            'is_followed_by_you',
            'has_subscription',
        ]
