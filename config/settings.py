from os import getenv
from os.path import join as join_path
from dotenv import load_dotenv

from pathlib import Path
from datetime import timedelta

from django.utils.translation import gettext_lazy as _
from firebase_admin import initialize_app, credentials

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(int(getenv('DEBUG')))

ALLOWED_HOSTS = ['*']

# CORS
CORS_ALLOW_ALL_ORIGINS = True

# Application definition
INSTALLED_APPS = [
    'channels',
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # libs
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'corsheaders',
    'debug_toolbar',
    'storages',
    'fcm_django',

    # apps
    'apps.authentication',
    'apps.integrations',
    'apps.files',
    'apps.content',
    'apps.chat',
    'startup.apps.StartupConfig',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': getenv('DB_NAME'),
        'USER': getenv('DB_USER'),
        'PASSWORD': getenv('DB_PASSWORD'),
        'HOST': getenv('DB_HOST'),
        'PORT': getenv('DB_PORT'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'authentication.User'

# Internationalization
LANGUAGE_CODE = 'ru-ru'
LANGUAGES = [
    ('uz', _('Uzbek')),
    ('ru', _('Russian')),
]

# TIME_ZONE = 'UTC'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [
    join_path(BASE_DIR, 'locale'),
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
# STATICFILES_DIRS = [
#     join_path(BASE_DIR, 'static')
# ]
STATIC_ROOT = join_path(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = join_path(BASE_DIR, 'media')
FILE_UPLOAD_DIR = join_path(MEDIA_ROOT, 'uploads')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# RestFramework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'EXCEPTION_HANDLER': 'config.core.api_exceptions.uni_exception_handler',
}

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

AWS_ACCESS_KEY_ID = getenv('MINIO_USERNAME')
AWS_SECRET_ACCESS_KEY = getenv('MINIO_PASSWORD')
AWS_STORAGE_BUCKET_NAME = 'sapi'
AWS_S3_ENDPOINT_URL = getenv('MINIO_URL')
AWS_S3_FILE_OVERWRITE = False
AWS_S3_VERIFY = False  # Optional: disable SSL cert verification
AWS_DEFAULT_ACL = None  # Optional: use None for default ACL
# AWS_S3_CUSTOM_DOMAIN = 'api.sapi.uz'
AWS_S3_USE_SSL = False
AWS_QUERYSTRING_AUTH = False

# SMS Integration
SMS_INTEGRATION_SETTINGS = {
    'SMS_BASE_URL': getenv('SMS_BASE_URL'),
    'SMS_USERNAME': getenv('SMS_USERNAME'),
    'SMS_PASSWORD': getenv('SMS_PASSWORD'),
}

# MULTIBANK
MULTIBANK_INTEGRATION_SETTINGS = {
    'PROD': {
        'BASE_URL': getenv('MULTIBANK_PROD_BASE_URL'),
        'APPLICATION_ID': getenv('MULTIBANK_PROD_APPLICATION_ID'),
        'STORE_ID': getenv('MULTIBANK_PROD_STORE_ID'),
        'MERCHANT_ID': getenv('MULTIBANK_PROD_MERCHANT_ID'),
        'SECRET': getenv('MULTIBANK_PROD_SECRET'),
    },
    'DEV': {
        'BASE_URL': getenv('MULTIBANK_DEV_BASE_URL'),
        'APPLICATION_ID': getenv('MULTIBANK_DEV_APPLICATION_ID'),
        'STORE_ID': getenv('MULTIBANK_DEV_STORE_ID'),
        'MERCHANT_ID': getenv('MULTIBANK_DEV_MERCHANT_ID'),
        'SECRET': getenv('MULTIBANK_DEV_SECRET'),
    }
}

# FIREBASE
FCM_CONFIG = {
    'type': 'service_account',
    'project_id': getenv('FIREBASE_PROJECT_ID'),
    'private_key_id': getenv('FIREBASE_PRIVATE_KEY_ID'),
    'private_key': getenv('FIREBASE_PRIVATE_KEY'),
    'client_email': getenv('FIREBASE_CLIENT_EMAIL'),
    'client_id': getenv('FIREBASE_CLIENT_ID'),
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
    'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40sapi-72000.iam.gserviceaccount.com',
    'universe_domain': 'googleapis.com'
}

cred = credentials.Certificate(FCM_CONFIG)
FIREBASE_APP = initialize_app(cred)

FCM_DJANGO_SETTINGS = {
    "DEFAULT_FIREBASE_APP": None,
    "APP_VERBOSE_NAME": 'SAPI',
    "ONE_DEVICE_PER_USER": True,
    "DELETE_INACTIVE_DEVICES": True,
}

# Debug Toolbar
if DEBUG:
    def show_toolbar(request):
        return True


    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": show_toolbar,
    }

    INTERNAL_IPS = [
        "127.0.0.1",
        "backend.sapi.uz",
    ]

# Swagger
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'api_key': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization'
        }
    },
}
if not DEBUG:
    # SWAGGER_SETTINGS['DEFAULT_API_URL'] = 'http://195.26.243.201:8080'
    SWAGGER_SETTINGS['DEFAULT_API_URL'] = 'https://api.sapi.uz'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',  # For development
        # OR for production with Redis:
        # 'BACKEND': 'channels_redis.core.RedisChannelLayer',
        # 'CONFIG': {
        #     'hosts': [('redis', 6379)],  # Or your Redis server address
        # },
    },
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(name)-12s %(levelname)-8s %(message)s'
        },
        'file': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'file',
            'filename': join_path(BASE_DIR, 'logs.log')
        }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['file']
        },
        'django.request': {
            'level': 'DEBUG',
            'handlers': ['file']
        }
    }
}

# SIMPLE-JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(days=1),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}
