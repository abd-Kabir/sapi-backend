from django.apps import AppConfig


class StartupConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'startup'

    def ready(self):
        from config.core.minio import ensure_minio_bucket

        ensure_minio_bucket()
