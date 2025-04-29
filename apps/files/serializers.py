from rest_framework import serializers

from apps.files.models import File


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = [
            'name',
            'size',
            'path',
        ]
