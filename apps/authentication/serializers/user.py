from rest_framework import serializers

from apps.authentication.models import User
from apps.files.serializers import FileSerializer


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
