from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status

from apps.authentication.models import User, SubscriptionPlan, UserSubscription, Donation, Fundraising
from apps.authentication.services import create_activity
from apps.files.serializers import FileSerializer
from apps.integrations.services.multibank import multibank_payment
from config.core.api_exceptions import APIValidation
from config.services import run_with_thread


class BecomeUserMultibankAddAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'multibank_account',
        ]


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
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    posts_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    subscribers_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    is_followed_by_you = serializers.SerializerMethodField()
    is_blocked_by_you = serializers.SerializerMethodField()
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

    def get_is_blocked_by_you(self, obj):
        user = self.context['request'].user
        return obj.is_blocked_by_user(user)

    def get_has_subscription(self, obj):
        user = self.context['request'].user
        return obj.has_subscription(user)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'is_creator',
            'category_id',
            'category_name',
            'creator_description',
            'profile_photo_info',
            'profile_banner_photo_info',
            'posts_count',
            'followers_count',
            'subscribers_count',
            'is_following',
            'is_followed_by_you',
            'is_blocked_by_you',
            'has_subscription',
        ]


class UserSubscriptionPlanListSerializer(serializers.ModelSerializer):
    banner = FileSerializer(read_only=True, allow_null=True)
    is_subscribed = serializers.SerializerMethodField(allow_null=True)

    def get_is_subscribed(self, obj):
        user: User = self.context['request'].user
        return user.subscriptions.filter(plan=obj).exists()

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'name',
            'description',
            'price',
            'banner',
            'is_subscribed',
            'created_at',
        ]


class UserFundraisingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fundraising
        fields = [
            'id',
            'title',
            'description',
            'goal',
            'deadline',
            'minimum_donation',
            'current_amount',
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

    def validate(self, attrs):
        user = self.context['request'].user
        card = attrs.get('subscriber_card')
        if card.user != user:
            raise APIValidation(_('Карта не найдена'), status_code=status.HTTP_400_BAD_REQUEST)
        return super().validate(attrs)

    def create(self, validated_data):
        with transaction.atomic():
            request = self.context['request']
            plan: SubscriptionPlan = validated_data.get('plan')
            card = validated_data.get('subscriber_card')
            creator = plan.creator
            end_date = now() + plan.duration
            subscriber = request.user
            amount = plan.price

            if self.check_subscription(validated_data):
                raise APIValidation(_('У вас уже имеется этот подписка'), status_code=400)
            subscription = UserSubscription.objects.create(subscriber=subscriber, creator=creator, end_date=end_date,
                                                           **validated_data)
            payment_info = multibank_payment(subscriber, creator, card, amount, 'subscription')
            subscription.payment_reference = payment_info
            subscription.save(update_fields=['payment_reference'])
            run_with_thread(create_activity, ('subscribed', None, subscription.id, subscriber, creator))
            return subscription

    class Meta:
        model = UserSubscription
        fields = [
            'id',
            'plan',
            'subscriber_card',
            'commission_by_subscriber',
        ]


class DonationCreateSerializer(serializers.ModelSerializer):
    # fundraising_id = serializers.IntegerField(required=False, allow_null=True)
    # creator_id = serializers.IntegerField(required=True)

    class Meta:
        model = Donation
        fields = [
            'amount',
            'message',
            'card',
            'fundraising',
            'creator',
        ]

    @staticmethod
    def get_creator(pk):
        try:
            return User.objects.get(pk=pk)
        except:
            raise APIValidation(_('Контент креатор не найден'), status_code=404)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['payment_info'] = instance.payment_info
        return representation

    def create(self, validated_data):
        with transaction.atomic():
            donator = self.context['request'].user
            creator = validated_data.get('creator')
            card = validated_data.get('card')
            fundraising = validated_data.get('fundraising')
            if fundraising:
                if fundraising.minimum_donation and fundraising.minimum_donation > validated_data.get('amount', 0):
                    raise APIValidation(_(f'Минимальный донат является: {validated_data.get("amount", 0)}'),
                                        status_code=400)
                if fundraising.deadline < now():
                    raise APIValidation(_('Срок сбора средств прошел'), status_code=400)
            if creator.minimum_message_donation > validated_data.get('amount', 0):
                validated_data['message'] = None
            validated_data['donator'] = donator
            donation = super().create(validated_data)
            payment_info = multibank_payment(donator, creator, card, validated_data.get('amount', 0), 'donation', fundraising)
            donation.payment_info = payment_info
            run_with_thread(create_activity, ('donation', None, donation.id, donator, validated_data.get('creator_id')))
            return donation
