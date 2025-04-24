from django.db import models
from django.db.models.fields.files import FieldFile


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        abstract = True

class CustomFieldFile(FieldFile):
    def custom_url(self, request):
        host = request.META.get('HTTP_HOST', '')
        return f"http://{host}/media/{self.name}"


class UrlFileField(models.FileField):
    attr_class = CustomFieldFile

# Usage example:
# file = UrlFileField(storage=S3Boto3Storage(), upload_to='files/')

