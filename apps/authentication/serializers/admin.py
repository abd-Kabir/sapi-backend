from rest_framework import serializers

from apps.authentication.models import User


class AdminCreatorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'phone_number',
            'sapi_share',
            'multibank_account',
        ]


class AdminCreatorUpdateSAPIShareSerializer(serializers.Serializer):
    sapi_share = serializers.IntegerField()
