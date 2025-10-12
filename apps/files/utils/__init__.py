import io
import logging
import mimetypes
import sys
import time
import uuid
from os import sep
from os.path import join as join_path

from PIL import Image
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from dotenv import load_dotenv
from rest_framework import status

from apps.files.models import File
from config.core.api_exceptions import APIValidation
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


def compress_image(file, quality=50):
    """
    Compress uploaded image using Pillow before saving.
    Converts all formats to JPEG for better compression.
    """
    try:
        image = Image.open(file)
        image_io = io.BytesIO()

        # Convert to RGB (to avoid issues with PNG/transparency)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')

        image.save(image_io, format='JPEG', quality=quality, optimize=True)
        image_io.seek(0)

        compressed = InMemoryUploadedFile(
            image_io,
            field_name='file',
            name=f"{file.name.rsplit('.', 1)[0]}.jpg",
            content_type='image/jpeg',
            size=sys.getsizeof(image_io),
            charset=None
        )
        return compressed
    except Exception as e:
        logger.warning(f'Image compression failed: {e}')
        return file  # fallback to original if something goes wrong


def upload_file(file):
    try:
        with transaction.atomic():
            if hasattr(file, 'content_type') and 'image' in file.content_type:
                file = compress_image(file)

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
            # with open(join_path('media', 'uploads', gen_name.replace(sep, '/')), 'wb+') as destination:
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
