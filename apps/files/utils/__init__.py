import logging

from django.conf import settings
from rest_framework import status

from apps.files.models import File
from config.core.api_exceptions import APIValidation

from os.path import join as join_path
from os import sep

from dotenv import load_dotenv
import uuid
import time

load_dotenv()
logger = logging.getLogger()


def get_extension(filename: str) -> str:
    return filename.split(".")[-1]


def unique_code() -> str:
    return "%s%s" % (time.time_ns(), str(uuid.uuid4()).replace("-", ""))


def upload_path() -> str:
    return settings.FILE_UPLOAD_DIR


def media_path(file_name):
    return join_path('media', 'uploads', file_name)


def gen_new_name(file) -> str:
    return "%s.%s" % (unique_code(), get_extension(filename=file.name))


def gen_hash_name(filename) -> str:
    return "%s.%s" % (unique_code(), get_extension(filename=filename))


def upload_file(file):
    try:
        name = file.name
        size = file.size
        gen_name = gen_new_name(file)
        content_type = file.content_type
        extension = get_extension(filename=file.name)
        path = media_path(gen_name)
        uploaded_file = File(name=name,
                             size=size,
                             gen_name=gen_name,
                             path=path,
                             content_type=content_type,
                             extension=extension)
        with open(join_path(upload_path(), gen_name.replace(sep, '/')), 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        uploaded_file.save()

        return uploaded_file
    except Exception as exc:
        logger.debug(f'file_upload_failed: {exc.__doc__}')
        raise APIValidation(detail=f"{exc.__doc__} - {exc.args}", status_code=status.HTTP_400_BAD_REQUEST)
