"""
Django settings for pasture project.

Generated by 'django-admin startproject' using Django 3.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
import json
from pathlib import Path
from neomodel import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
RESOURCE_DIR = BASE_DIR.joinpath('resources')
STATIC_DIR = RESOURCE_DIR.joinpath('static')
TEMPLATE_DIR = RESOURCE_DIR.joinpath('templates')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
def get_secret(base_dir: Path):
    secret_file_path = base_dir.joinpath('configs/settings/secret.json')
    if not secret_file_path.exists():
        raise FileNotFoundError(f"Cant' find secret file in path({secret_file_path})")

    return json.load(secret_file_path.open('r'))


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
    'django_celery_results',
    'corsheaders',
    'rest_framework',
    'djangorestframework_camel_case',
    'drf_spectacular',
    'django_extensions',
    'django_filters',
    'pasture.dash',
    'pasture.assets',
    'pasture.portfolio',
    'django_neomodel',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pasture.configs.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR, ],
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

WSGI_APPLICATION = 'pasture.configs.wsgi.application'
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PARSER_CLASSES': (
        'djangorestframework_camel_case.parser.CamelCaseJSONParser',
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
    ),
}
SPECTACULAR_SETTINGS = {
    'TITLE': 'Pasture API Document',
    'DESCRIPTION': 'Pasture API documentation generated by drf-specatular',
    'CONTACT': {'name': 'shephexd', 'url': 'https://shephexd.github.io'},
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'filter': True,
    },
    'LICENSE': {
        'name': 'MIT License',
        'url': 'https://github.com/shephexd/pasture',
    },
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
SECRET = get_secret(BASE_DIR)
SECRET_KEY = SECRET['SECRET_KEY']

config.DATABASE_URL = SECRET['GRAPH_DB']["DATABASE_URL"]

NEOMODEL_SIGNALS = True
NEOMODEL_FORCE_TIMEZONE = False
NEOMODEL_MAX_CONNECTION_POOL_SIZE = 50

DATABASES = SECRET['DATABASES']
# Celery Configuration Options
for k, v in SECRET['CELERY'].items():
    locals()[f"CELERY_{k}"] = v

# django cache setting.
CACHES = SECRET['CACHES']

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# DEBUG MODE
if DEBUG:
    CELERY_ALWAYS_EAGER = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
STATIC_URL = '/static/'
