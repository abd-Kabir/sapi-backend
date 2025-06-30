from rest_framework import serializers

from apps.authentication.models import SubscriptionPlan, Card, Fundraising
from apps.files.serializers import FileSerializer
from apps.integrations.services.sms_services import verify_sms_code


class DeleteAccountVerifySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6, required=True)

    def validate(self, attrs):
        user = self.context['request'].user
        sms = attrs.get('code')
        verify_sms_code(user, sms)
        return super().validate(attrs)


class MyCardListSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Card
        fields = [
            'id',
            'card_pan',
            'is_main',
            'type',
            'type_display',
        ]


class AddCardSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def create(self, validated_data):
        is_main = validated_data.pop('is_main', False)
        expiration = validated_data.pop('expiration', None).replace('/', '')
        number = validated_data.pop('number', None)
        if not Card.objects.filter(user=validated_data.get('user')).exists():
            is_main = True
        card, _ = Card.objects.update_or_create(number=number, defaults={**validated_data})
        card.expiration = expiration
        card.set_main(is_main)
        return card

    class Meta:
        model = Card
        fields = [
            'id',
            'is_main',
            'number',
            'expiration',
            'cvc_cvv',
            'user',
        ]


class MySubscriptionPlanListSerializer(serializers.ModelSerializer):
    banner = FileSerializer(read_only=True, allow_null=True)

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'is_active',
            'name',
            'description',
            'price',
            # 'duration',
            'banner',
        ]


class AddSubscriptionPlanSerializer(serializers.ModelSerializer):
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def create(self, validated_data):
        instance: SubscriptionPlan = super().create(validated_data)
        instance.set_duration()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['banner'] = FileSerializer(instance.banner).data if instance.banner else None
        return representation

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'is_active',
            'name',
            'description',
            'price',
            # 'duration',
            'creator',
            'banner',
        ]


class MySubscriptionPlanRetrieveUpdateSerializer(serializers.ModelSerializer):
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['banner'] = FileSerializer(instance.banner).data if instance.banner else None
        return representation

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'is_active',
            'name',
            'description',
            'price',
            # 'duration',
            'creator',
            'banner',
        ]


class FundraisingSerializer(serializers.ModelSerializer):
    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Fundraising
        fields = [
            'id',
            'title',
            'description',
            'goal',
            'deadline',
            'minimum_donation',
            'creator',
            'current_amount',
        ]


class FollowersDashboardByPlanSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    subscriber_count = serializers.IntegerField()
    percent = serializers.FloatField()
