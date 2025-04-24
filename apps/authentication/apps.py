from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.authentication'

    # def ready(self):
    #     from config.core.minio import ensure_minio_bucket
    #
    #     ensure_minio_bucket()
