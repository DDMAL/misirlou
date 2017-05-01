"""
Django settings for misirlou project.

Generated by 'django-admin startproject' using Django 1.8.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from datetime import timedelta

"""
These are pre-defined setting levels. You set SETTING_TYPE
to one of these in order to automatically configure settings.

LOCAL:
    * Constants can be read from this file for database password,
    secret key, etc. No need to replicate the servers dir-structure.
    * Debug is set to true.
    * Overrides for any setting in this file can be specified in a an
    optional elvis.local_settings module.

DEVELOPMENT:
    * Constants and privileged information must be read in from
    plain text files placed in the same structure as on the server.
    * Debug is set to true.
    * Overrides can not be specified.

PRODUCTION:
    * Like development, but debug set to false.

"""

PRODUCTION = 0
DEVELOPMENT = 1
LOCAL = 2
SETTING_TYPE = LOCAL
assert SETTING_TYPE in [PRODUCTION, DEVELOPMENT, LOCAL], "Must choose a legal setting type."

# Used to build up paths using the musiclibs folder as a base.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The directories where the server expects to find config files, when not in LOCAL.
DB_PASS_PATH = '/srv/webapps/musiclibs/config/db_pass'
SECRET_KEY_PATH = '/srv/webapps/musiclibs/config/secret_key'

if SETTING_TYPE is LOCAL:
    DEBUG = True
else:
    DEBUG = False

if SETTING_TYPE is PRODUCTION:
    ALLOWED_HOSTS = ['musiclibs.net', 'www.musiclibs.net']
elif SETTING_TYPE is DEVELOPMENT:
    ALLOWED_HOSTS = ['dev.musiclibs.net']
else:
    ALLOWED_HOSTS = []

# If production, set up SSL settings.
if SETTING_TYPE is PRODUCTION:

    # Security settings.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_SSL_REDIRECT = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_SSL_REDIRECT = True

if SETTING_TYPE is not LOCAL:
    # Passwords stored in un-committed text files.
    with open(SECRET_KEY_PATH) as f:
        SECRET_KEY = f.read().strip()
    with open(DB_PASS_PATH) as f:
        DB_PASS = f.read().strip()
else:
    SECRET_KEY = ""
    DB_PASS_PATH = ""

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'misirlou',
    'rest_framework',
    'django_extensions',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'misirlou.urls'

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

WSGI_APPLICATION = 'misirlou.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

# Database definition for server.
if SETTING_TYPE is not LOCAL:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'musiclibs_db',
            'USER': 'musiclibs',
            'PASSWORD': DB_PASS,
            'HOST': 'localhost',
        }
    }

# Solr settings
SOLR_MAIN_CORE = "musiclibs"
SOLR_SERVER = "http://localhost:8983/solr/{}/".format(SOLR_MAIN_CORE)
SOLR_OCR_CORE = "musiclibs_ocr"
SOLR_OCR = "http://localhost:8983/solr/{}/".format(SOLR_OCR_CORE)
SOLR_TEST = "http://localhost:8983/solr/misirlou_test/"

# Metadata mappings
reverse_map = {
    'title': ['title', 'titles', 'title(s)', 'titre', 'full title'],
    'author': ['author', 'authors', 'author(s)', 'creator'],
    'date': ['date', 'period', 'publication date', 'publish date'],
    'location': ['location'],
    'language': ['language'],
    'repository': ['repository']
}

SOLR_MAP = {}
for k, v in reverse_map.items():
    for vi in v:
        SOLR_MAP[vi] = k

# Status codes
ERROR = -1
SUCCESS = 0
PROGRESS = 1

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = (
    ('js', os.path.join(BASE_DIR, 'misirlou/frontend/js')),
)
STATIC_ROOT = "/srv/webapps/musiclibs/static/"

DEBUG_CLIENT_SIDE = False

# Celery Settings
# ===============
BROKER_URL = 'amqp://'
REDIS_SERVER = 1
REDIS_PORT = 6379
REDIS_HOST = 'localhost'
CELERY_RESULT_BACKEND = 'redis://{}/{}'.format(REDIS_HOST, str(REDIS_SERVER))
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_REDIS_MAX_CONNECTIONS = 1000
CELERY_TIMEZONE = 'UTC'

# Route celery settings for different configs.
if SETTING_TYPE:
    CELERY_QUEUE_DICT = {
        "import": {'queue': 'musiclibs_import'},
        "test": {'queue': 'musiclibs_test'}
    }
    CELERY_ROUTES = {'misirlou.tasks.import_single_manifest': CELERY_QUEUE_DICT['import'],
                     'misirlou.tasks.test_manifest': CELERY_QUEUE_DICT['test']}
    CELERY_RESULT_BACKEND = 'redis://{}/{}'.format(REDIS_HOST, str(REDIS_SERVER))

# Logging settings
if SETTING_TYPE:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': '/var/log/musiclibs/django.log'
            },
        },
        'loggers': {
            'django.request': {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': True,
            },
        },
    }

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100
}

try:
    from misirlou.local_settings import *
except ImportError:
    pass
