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
