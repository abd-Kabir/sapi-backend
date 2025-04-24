from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from storages.backends.s3boto3 import S3Boto3Storage
from django.http import FileResponse

from config.core.api_exceptions import APIValidation


class MediaPath(APIView):
    permission_classes = [AllowAny, ]

    @staticmethod
    def get(request, path):
        try:
            storage = S3Boto3Storage()
            file = storage.open(path)
            return FileResponse(file)
        except Exception as e:
            raise APIValidation(e.args, status_code=status.HTTP_404_NOT_FOUND)
