import logging
import mimetypes

from django.conf import settings
from django.db import transaction
from rest_framework import status

from apps.files.models import File
from config.core.api_exceptions import APIValidation

from os.path import join as join_path
from os import sep

from dotenv import load_dotenv
import uuid
import time

from config.core.minio import s3_client

load_dotenv()
logger = logging.getLogger()


def get_extension(filename: str) -> str:
    return filename.split(".")[-1]


def unique_code() -> str:
    return "%s%s" % (time.time_ns(), str(uuid.uuid4()).replace("-", ""))


def upload_path(file_name) -> str:
    return join_path('uploads', file_name)


def media_path(file_name):
    return join_path('media', 'uploads', file_name)


def gen_new_name(file) -> str:
    return "%s.%s" % (unique_code(), get_extension(filename=file.name))


def gen_hash_name(filename) -> str:
    return "%s.%s" % (unique_code(), get_extension(filename=filename))


def upload_file(file):
    try:
        with transaction.atomic():
            name = file.name
            size = file.size
            gen_name = gen_new_name(file)
            extra_content_type, encoding = mimetypes.guess_type(file.name)
            content_type = file.content_type if hasattr(file, 'content_type') else extra_content_type
            extension = get_extension(filename=file.name)
            path = media_path(gen_name)
            s3_path = upload_path(gen_name)

            s3_client.upload_fileobj(
                file,
                settings.AWS_STORAGE_BUCKET_NAME,
                s3_path,
                ExtraArgs={
                    'ContentType': content_type,
                    # 'ACL': 'private' # or whatever ACL you need
                }
            )

            uploaded_file = File(name=name,
                                 size=size,
                                 gen_name=gen_name,
                                 path=path,
                                 content_type=content_type,
                                 extension=extension)
            # with open(join_path(upload_path(), gen_name.replace(sep, '/')), 'wb+') as destination:
            #     for chunk in file.chunks():
            #         destination.write(chunk)
            uploaded_file.save()

            return uploaded_file
    except Exception as exc:
        logger.debug(f'file_upload_failed: {exc.__doc__}')
        raise APIValidation(detail=f"{exc.__doc__} - {exc.args}", status_code=status.HTTP_400_BAD_REQUEST)

def delete_file(file: File):
    # file = s3_client.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=f'uploads/{file.gen_name}')
    # print(file)
    return s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=f'uploads/{file.gen_name}')
