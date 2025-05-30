import logging
# from os import remove as delete_file

from django.utils.translation import gettext_lazy as _
from django.http import Http404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.files.models import File
from apps.files.utils import upload_file, delete_file
from config.core.api_exceptions import APIValidation

logger = logging.getLogger()


class FileCreateAPIView(APIView):
    parser_classes = [MultiPartParser, ]
    permission_classes = [AllowAny, ]

    @swagger_auto_schema(
        operation_description='Upload file',
        manual_parameters=[
            openapi.Parameter(
                'file', in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description=_('Файл для загрузки (максимальный размер 50 МБ)')
            ),
        ]
    )
    def post(self, request):
        file = request.data.get('file')
        if not file:
            raise APIValidation(detail=_('Файл не был отправлен'), code=status.HTTP_400_BAD_REQUEST)

        if file.size > 20_971_520:
            raise APIValidation(detail=_('Размер файла превысил 20 МБ!'), code=status.HTTP_400_BAD_REQUEST)

        e_file = upload_file(file=file)
        return Response({
            'message': _('Файл успешно загружен'),
            'file': e_file.id,
            'path': e_file.path,
            'status': status.HTTP_201_CREATED
        }, status=status.HTTP_201_CREATED)


class FileDeleteAPIView(APIView):
    permission_classes = [AllowAny, ]

    @staticmethod
    def get_object(pk):
        try:
            return File.objects.get(pk=pk)
        except File.DoesNotExist:
            raise Http404

    def delete(self, request, pk):
        file = self.get_object(pk)
        delete_file(file)
        file.delete()
        return Response({
            'message': _('Файл успешно удален'),
            'status': status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
