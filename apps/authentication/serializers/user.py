from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status

from apps.authentication.models import User, SubscriptionPlan, UserSubscription, Donation, Fundraising
from apps.authentication.services import create_activity
from apps.files.serializers import FileSerializer
from apps.integrations.services.multibank import multibank_payment, calculate_payment_amount
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
    category_name_uz = serializers.CharField(source='category.name_uz', read_only=True, allow_null=True)
    category_name_en = serializers.CharField(source='category.name_en', read_only=True, allow_null=True)
    category_name_ru = serializers.CharField(source='category.name_ru', read_only=True, allow_null=True)
    plan_names = serializers.SerializerMethodField()

    @staticmethod
    def get_plan_names(obj):
        if hasattr(obj, 'plan_names'):
            return ', '.join(obj.plan_names) if obj.plan_names else None
        return None

    class Meta:
        model = User
        fields = [
            'id',
            'category',
            'category_name',
            'category_name_uz',
            'category_name_en',
            'category_name_ru',
            'username',
            'plan_names',
            'creator_description',
            'profile_photo',
            'profile_photo_info',
            'profile_banner_photo',
            'profile_banner_photo_info',
        ]


class UserRetrieveSerializer(serializers.ModelSerializer):
    donation_banner_info = FileSerializer(read_only=True, allow_null=True, source='donation_banner')
    profile_photo_info = FileSerializer(read_only=True, allow_null=True, source='profile_photo')
    profile_banner_photo_info = FileSerializer(read_only=True, allow_null=True, source='profile_banner_photo')
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    category_name_uz = serializers.CharField(source='category.name_uz', read_only=True, allow_null=True)
    category_name_en = serializers.CharField(source='category.name_en', read_only=True, allow_null=True)
    category_name_ru = serializers.CharField(source='category.name_ru', read_only=True, allow_null=True)
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
            'category_name_uz',
            'category_name_en',
            'category_name_ru',
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

            'minimum_message_donation',
            'max_donation_letters',
            'show_donation_amount',
            'donation_banner_info',
        ]


class UserSubscriptionPlanListSerializer(serializers.ModelSerializer):
    banner = FileSerializer(read_only=True, allow_null=True)
    is_subscribed = serializers.SerializerMethodField(allow_null=True)
    commission = serializers.SerializerMethodField(allow_null=True)

    def get_is_subscribed(self, obj):
        user: User = self.context['request'].user
        return user.subscriptions.filter(plan=obj).exists()

    @staticmethod
    def get_commission(obj):
        creator_amount, amount, sapi_amount = calculate_payment_amount(amount=obj.price,
                                                                       sapi_share=obj.creator.sapi_share,
                                                                       commission_by_subscriber=True)
        return amount - creator_amount

    def to_representation(self, instance):
        user = self.context['request'].user
        representation = super().to_representation(instance)
        if user.is_admin:
            representation['is_deleted'] = instance.is_deleted
            representation['is_active'] = instance.is_active
        return representation

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'name',
            'description',
            'price',
            'banner',
            'is_subscribed',
            'commission',
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

    def check_subscription(self, validated_data, creator):
        request = self.context['request']
        subscriber = request.user
        plan = validated_data.get('plan')
        user_subs = UserSubscription.objects.filter(
            subscriber=subscriber,
            plan=plan,
        )
        if user_subs.filter(end_date__gte=timezone.now()).exists():
            raise APIValidation(_('У вас уже имеется этот подписка'), status_code=400)
        if user_subs.filter(creator=creator).exists():
            raise APIValidation(
                _('У вас уже имеется этот подписка. Срок ее действия истек, можете активировать ее в своем профиле.'),
                status_code=400
            )

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
            commission_by_subscriber = validated_data.get('commission_by_subscriber')

            self.check_subscription(validated_data, creator)
            # raise APIValidation(_('У вас уже имеется этот подписка'), status_code=400)
            subscription = UserSubscription.objects.create(subscriber=subscriber, creator=creator, end_date=end_date,
                                                           **validated_data)
            payment_info = multibank_payment(subscriber, creator, card, amount, 'subscription',
                                             commission_by_subscriber=commission_by_subscriber,
                                             subscription=subscription)
            subscription.payment_reference = payment_info
            subscription.save(update_fields=['payment_reference', 'is_active'])
            run_with_thread(create_activity, ('subscribed', None, subscription.id, subscriber, creator))
            return subscription

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['payment_reference'] = instance.payment_reference
        return representation

    class Meta:
        model = UserSubscription
        fields = [
            'id',
            'plan',
            'subscriber_card',
            'commission_by_subscriber',
            'one_time',
        ]


class DonationCreateSerializer(serializers.ModelSerializer):
    # fundraising_id = serializers.IntegerField(required=False, allow_null=True)
    # creator_id = serializers.IntegerField(required=True)

    class Meta:
        model = Donation
        fields = [
            'amount',
            'message',
            'commission_by_subscriber',
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
            commission_by_subscriber = validated_data.get('commission_by_subscriber')
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
            if creator.max_donation_letters:
                validated_data['message'] = validated_data['message'][:creator.max_donation_letters]
            validated_data['donator'] = donator
            donation = super().create(validated_data)
            payment_info = multibank_payment(donator, creator, card, validated_data.get('amount', 0), 'donation',
                                             fundraising, commission_by_subscriber=commission_by_subscriber,
                                             donation=donation)
            donation.payment_info = payment_info
            donation.save()
            run_with_thread(create_activity, ('donation', None, donation.id, donator, validated_data.get('creator_id')))
            return donation


class CalculatePaymentCommissionSerializer(serializers.Serializer):
    amount = serializers.IntegerField(required=True)
    creator_id = serializers.IntegerField(required=True)


class ConfigureDonationSettingsSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        user = self.context['request'].user
        user.minimum_message_donation = validated_data.get('minimum_message_donation', user.minimum_message_donation)
        user.donation_banner = validated_data.get('donation_banner', user.donation_banner)
        user.max_donation_letters = validated_data.get('max_donation_letters', user.max_donation_letters)
        user.show_donation_amount = validated_data.get('show_donation_amount', user.show_donation_amount)
        user.save(update_fields=['minimum_message_donation', 'donation_banner', 'max_donation_letters'])
        return user

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['donation_banner'] = FileSerializer(
            instance.donation_banner).data if instance.donation_banner else None
        return representation

    class Meta:
        model = User
        fields = [
            'id',
            'minimum_message_donation',
            'donation_banner',
            'max_donation_letters',
            'show_donation_amount',
        ]
