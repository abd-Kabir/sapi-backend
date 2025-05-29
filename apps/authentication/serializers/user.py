from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.authentication.models import User, SubscriptionPlan, UserSubscription, Donation
from apps.authentication.services import create_activity
from apps.files.serializers import FileSerializer
from config.core.api_exceptions import APIValidation
from config.services import run_with_thread


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
        return obj.followers_count()

    @staticmethod
    def get_subscribers_count(obj):
        return obj.subscribers_count()

    def get_is_following(self, obj):
        user = self.context['request'].user
        return obj.is_following(user)

    def get_is_followed_by_you(self, obj):
        user = self.context['request'].user
        return obj.is_followed_by(user)

    def get_has_subscription(self, obj):
        user = self.context['request'].user
        return obj.has_subscription(user)

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


class UserSubscriptionPlanListSerializer(serializers.ModelSerializer):
    banner = FileSerializer(read_only=True, allow_null=True)

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'name',
            'description',
            'price',
            'banner',
        ]


class UserSubscriptionCreateSerializer(serializers.ModelSerializer):

    def check_subscription(self, validated_data):
        request = self.context['request']
        subscriber = request.user
        plan = validated_data.get('plan')
        user_subs = UserSubscription.objects.filter(
            subscriber=subscriber,
            plan=plan,
            is_active=True,
            end_date__gte=timezone.now(),
        ).exists()
        return user_subs

    def create(self, validated_data):
        request = self.context['request']
        plan = validated_data.get('plan')
        creator = plan.creator
        end_date = now() + plan.duration
        subscriber = request.user

        if self.check_subscription(validated_data):
            raise APIValidation(_('У вас уже имеется этот подписка'), status_code=400)
        subscription = UserSubscription.objects.create(subscriber=subscriber, creator=creator, end_date=end_date,
                                                       **validated_data)
        run_with_thread(create_activity, ('subscribed', None, subscription.id, subscriber, creator))
        return subscription

    class Meta:
        model = UserSubscription
        fields = [
            'id',
            'plan',
            'commission_by_subscriber',
        ]


class DonationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = [
            'amount',
            'message',
            'creator_id',
        ]

    @staticmethod
    def get_creator(pk):
        try:
            return User.objects.get(pk=pk)
        except:
            raise APIValidation(_('Контент креатор не найден'), status_code=404)

    def create(self, validated_data):
        donater = self.context['request'].user
        creator = self.get_creator(validated_data.get('creator_id'))
        if creator.minimum_message_donation > validated_data.get('amount', 0):
            validated_data['message'] = None
        validated_data['donator'] = donater
        donation = super().create(validated_data)
        run_with_thread(create_activity, ('donation', None, donation.id, donater, validated_data.get('creator_id')))
        return donation
