import boto3
from botocore.config import Config
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from storages.backends.s3boto3 import S3Boto3Storage
from django.http import FileResponse, StreamingHttpResponse, Http404

from config.core.api_exceptions import APIValidation


class BaseModelViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, ]
    filter_backends = [DjangoFilterBackend, OrderingFilter, ]
    ordering = ['created_at']
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']


class MediaPath(APIView):
    permission_classes = [AllowAny, ]

    # @staticmethod
    # def get(request, path):
    #     try:
    #         storage = S3Boto3Storage()
    #         file = storage.open(path)
    #         return FileResponse(file)
    #     except Exception as e:
    #         raise APIValidation(e.args, status_code=status.HTTP_404_NOT_FOUND)
    def get(self, request, path):
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            config=Config(signature_version='s3v4'),
        )
        bucket = settings.AWS_STORAGE_BUCKET_NAME

        range_header = request.headers.get('Range')
        try:
            extra_args = {}
            if range_header:
                extra_args['Range'] = range_header

            obj = s3.get_object(Bucket=bucket, Key=path, **extra_args)

            resp = StreamingHttpResponse(obj['Body'].iter_chunks(), status=206 if range_header else 200)
            resp['Content-Type'] = obj['ContentType']
            resp['Accept-Ranges'] = 'bytes'

            if 'ContentRange' in obj:
                resp['Content-Range'] = obj['ContentRange']
            if 'ContentLength' in obj:
                resp['Content-Length'] = str(obj['ContentLength'])

            return resp
        except Exception as e:
            raise Http404('File not found')


class AppleJSAPIView(APIView):
    permission_classes = [AllowAny, ]

    def get(self, request, *args, **kwargs):
        return Response({
            "applinks": {
                "apps": [],
                "details": [
                    {
                        "appIDs": [
                            "QDCS6A57GJ.app.sapi"
                        ],
                        "paths": [
                            "*"
                        ]
                    }
                ]
            },
            "webcredentials": {
                "apps": [
                    "QDCS6A57GJ.app.sapi"
                ]
            }
        })
