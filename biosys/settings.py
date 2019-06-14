"""
Django settings for biosys project.
"""
from __future__ import absolute_import, unicode_literals, print_function, division

import os
import sys

from confy import env, database
from unipath import Path

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(__file__).ancestor(2)
PROJECT_DIR = os.path.join(BASE_DIR, 'biosys')
# Add PROJECT_DIR to the system path.
sys.path.insert(0, PROJECT_DIR)
# Add PROJECT_DIR/apps to the system path.
sys.path.insert(0, os.path.join(PROJECT_DIR, 'apps'))

# Security settings
DEBUG = env('DEBUG', False)
SECRET_KEY = env('SECRET_KEY', 'wjdh^hIO)jj5')
CSRF_COOKIE_SECURE = env('CSRF_COOKIE_SECURE', False)
SESSION_COOKIE_SECURE = env('SESSION_COOKIE_SECURE', False)
ALLOWED_HOSTS = env('ALLOWED_HOSTS', [
    'localhost',
    '127.0.0.1',
    'biosys.dbca.wa.gov.au',
    'biosys.dbca.wa.gov.au.',
    'biosys-uat.dbca.wa.gov.au',
    'biosys-uat.dbca.wa.gov.au.',
])

# Application definition
# The variables below are added to all responses in biosys/context_processors.py
SITE_TITLE = 'BioSys - WA Biological Survey Database'
APPLICATION_VERSION_NO = '6.0.0'

INSTALLED_APPS = (
    'grappelli',  # Must be before django.contrib.admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django.contrib.postgres',

    'rest_framework',
    'rest_framework.authtoken',
    'dry_rest_permissions',
    'rest_framework_gis',
    'django_filters',
    'corsheaders',
    'drf_yasg',
    'reversion',
    'storages',
    'djoser',

    'django_extensions',
    'bootstrap3',
    'timezone_field'
)

PROJECT_APPS = (
    'main',
    'publish',
)

INSTALLED_APPS += PROJECT_APPS

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

EXTRA_MIDDLEWARE = env('EXTRA_MIDDLEWARE', [
    'dpaw_utils.middleware.SSOLoginMiddleware'
])

MIDDLEWARE += EXTRA_MIDDLEWARE

ROOT_URLCONF = 'biosys.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.request",
                "django.template.context_processors.tz",
                "django.template.context_processors.csrf",
                "django.contrib.messages.context_processors.messages",
                "biosys.context_processors.standard",
            ],
        },
    },
]

LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'
LOGIN_REDIRECT_URL = '/'

AUTHENTICATION_BACKENDS = env('AUTHENTICATION_BACKENDS', [
    'django.contrib.auth.backends.ModelBackend',
])

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': env('PASSWORD_MIN_LENGTH', 8),
        }
    },
]
EXTRA_PASSWORD_VALIDATORS = env('EXTRA_PASSWORD_VALIDATORS', [])
AUTH_PASSWORD_VALIDATORS += EXTRA_PASSWORD_VALIDATORS

EXPORTER_CLASS = env('EXPORTER_CLASS', 'main.api.exporters.DefaultExporter')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': env('REST_FRAMEWORK_DEFAULT_AUTHENTICATION_CLASSES', [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'main.api.authentication.NoCsrfSessionAuthentication',
    ]),
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        env('REST_FRAMEWORK_DEFAULT_PERMISSION_CLASS', 'rest_framework.permissions.AllowAny'),
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_METADATA_CLASS': 'rest_framework.metadata.SimpleMetadata',
    'DEFAULT_THROTTLE_RATES': {
        'auth': env('REST_FRAMEWORK_AUTH_THROTTLE', '20/hour'),
    }
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'basic': {
            'type': 'basic'
        },
        'api_key': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization'
        }
    },
    'USE_SESSION_AUTH': env('SWAGGER_USE_SESSION_AUTH', False),
    'APIS_SORTER': 'alpha',
}

CORS_ORIGIN_ALLOW_ALL = env('CORS_ORIGIN_ALLOW_ALL', False)
CORS_ALLOW_CREDENTIALS = env('CORS_ALLOW_CREDENTIALS', True)
CORS_ORIGIN_WHITELIST = env('CORS_ORIGIN_WHITELIST', [

])
CORS_ORIGIN_REGEX_WHITELIST = env('CORS_ORIGIN_WHITELIST', [
    r'^.*$',
])

WSGI_APPLICATION = 'biosys.wsgi.application'

# Database
if env('RDS_DB_NAME'):
    # AWS settings found
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': env('RDS_DB_NAME'),
            'USER': env('RDS_USERNAME'),
            'PASSWORD': env('RDS_PASSWORD'),
            'HOST': env('RDS_HOSTNAME'),
            'PORT': env('RDS_PORT'),
        }
    }
else:
    # look for a DATABASE_URL
    DATABASES = {
        'default': database.config(name='DATABASE_URL', default='postgis://postgres:postgres@localhost/biosys')
    }

# Internationalization
LANGUAGE_CODE = 'en-au'
TIME_ZONE = env('TIME_ZONE', 'Australia/Perth')
USE_I18N = True
USE_L10N = True
USE_TZ = True
# Set the formats that will be displayed in date fields
# If USE_L10N == True, then locale-dictated format has higher precedence.
DATE_FORMAT = '%d/%m/%Y'  # O5/10/2006
# Set the formats that will be accepted in date input fields
DATE_INPUT_FORMATS = (
    '%d/%m/%Y',  # '25/10/2006'
    '%Y-%m-%d',  # '2006-10-25'
    '%Y_%m_%d',  # '2006_10_25'
)

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
# Absolute path to the directory static files should be collected to.
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
# Ensure that the media directory exists:
if not os.path.exists(os.path.join(BASE_DIR, 'media')):
    os.mkdir(os.path.join(BASE_DIR, 'media'))
# Absolute filesystem path to the directory that will hold user-uploaded files.
MEDIA_ROOT = env('MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))
# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
MEDIA_URL = '/media/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(PROJECT_DIR, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

BOOTSTRAP3 = {
    'jquery_url': '//static.dbca.wa.gov.au/static/libs/jquery/2.2.1/jquery.min.js',
    'base_url': '//static.dbca.wa.gov.au/static/libs/twitter-bootstrap/3.3.6/',
    'css_url': None,
    'theme_url': None,
    'javascript_url': None,
    'javascript_in_head': False,
    'include_jquery': False,
    'required_css_class': 'required-form-field',
    'set_placeholder': False,
}

# The class that should provide a mapping between the species scientific name and the species name_id.
# To use the WA Herbarium web service set SPECIES_FACADE_CLASS='main.utils_species.HerbieFacade'
# in the environment file.
SPECIES_FACADE_CLASS = env('SPECIES_FACADE_CLASS', None)

# Logging settings
# Ensure that the logs directory exists:
LOG_FOLDER = env('LOG_FOLDER', os.path.join(BASE_DIR, 'logs'))
if not os.path.exists(LOG_FOLDER):
    os.mkdir(LOG_FOLDER)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'precise': {
            'format': '{%(asctime)s.%(msecs)d}  %(message)s [%(levelname)s %(name)s]',
            'datefmt': '%H:%M:%S'
        },
        'default': {
            'format': '%(asctime)s %(levelname)-8s [%(name)-15s] %(message)s',
            'datefmt': '%Y/%m/%d %H:%M:%S',
        },
        'import_legacy': {
            'format': '%(levelname)-8s %(message)s [%(asctime)s]',
            'datefmt': '%Y/%m/%d %H:%M:%S',
        }
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': env('LOG_FILE_LEVEL', 'WARNING'),
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_FOLDER, 'biosys.log'),
            'when': 'midnight',
            'backupCount': 2,
            'formatter': 'default',
        },
        'console': {
            'level': env('LOG_CONSOLE_LEVEL', 'WARNING'),
            'class': 'logging.StreamHandler',
            'formatter': 'precise',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': True
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        }
    }
}

# Grappelli settings
GRAPPELLI_ADMIN_TITLE = SITE_TITLE + ' administration'

# Email settings
EMAIL_HOST = env('EMAIL_HOST', 'localhost')
EMAIL_PORT = env('EMAIL_PORT', 25)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'webmaster@localhost')
EMAIL_HOST_USER = env('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env('EMAIL_USE_TLS', False)
EMAIL_USE_SSL = env('EMAIL_USE_SSL', False)
EMAIL_SUBJECT_PREFIX = env('EMAIL_SUBJECT_PREFIX', '[BioSys] ')
EMAIL_USE_LOCALTIME = env('EMAIL_USE_LOCALTIME', False)

SEND_REGISTRATION_CONF = env('SEND_REGISTRATION_CONF', False)
REGISTRATION_EMAIL_SUBJECT = env('REGISTRATION_EMAIL_SUBJECT', '')
REGISTRATION_EMAIL_BODY = env('REGISTRATION_EMAIL_BODY', '')
REGISTRATION_EMAIL_FROM = env('REGISTRATION_EMAIL_FROM', 'hello')

# djoser is used to manage user password reset workflow.
# see https://djoser.readthedocs.io
DJOSER = {
    'PASSWORD_RESET_CONFIRM_URL': env('PASSWORD_RESET_CONFIRM_URL', '#/reset-password/{uid}/{token}'),
    'PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND': env('PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND', True),
}
# This is use in the email template sent to the user after a reset password request.
# see https://django-templated-mail.readthedocs.io/en/latest/settings.html#site-name
# if not specified SITE_NAME and DOMAIN are set from the django.contrib.sites.shortcuts.get_current_site(request)
SITE_NAME = env('PASSWORD_RESET_SITE_NAME', 'BioSys')
DOMAIN = env('PASSWORD_RESET_DOMAIN')

###################################################################################
#  Static and media files settings
#  Change this settings to host you static or media
#  files on S3.
#  For other settings or storage options refer to:
#  https://django-storages.readthedocs.io/en/latest/index.html
####################################################################################
# static files
# for static on S3 use 'main.backends.storages.S3StaticStorage'
STATICFILES_STORAGE = env('STATICFILES_STORAGE', 'django.contrib.staticfiles.storage.StaticFilesStorage')
# if using S3 the next setting specifies a bucket 'folder' for the static files
STATICFILES_LOCATION = env('STATICFILES_LOCATION', 'static')
# media files
# for media on S3 use main.backends.storages.S3MediaStorage
DEFAULT_FILE_STORAGE = env('DEFAULT_FILE_STORAGE', 'django.core.files.storage.FileSystemStorage')
# if using S3 the next setting specifies a bucket 'folder' for the media files.
MEDIAFILES_LOCATION = env('MEDIAFILES_LOCATION', 'media')

# AWS settings
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', 'BUCKET_NAME')
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', 'ap-southeast-2')
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', 'xxxxxxxxxxxxxxxxxxxx')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', 'yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy')
S3_USE_SIGV4 = True

# If using a CDN or a S3 static website tell django-storages the domain to use to refer to static files.
# By default it is s3.<region>.amazonaws.com/<bucket>/...
AWS_S3_CUSTOM_DOMAIN = env('AWS_S3_CUSTOM_DOMAIN', None)

# For when the app is behind a proxy or a load balancer in charge of the https/ssl
# https://docs.djangoproject.com/en/2.1/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = env('SECURE_PROXY_SSL_HEADER')
USE_X_FORWARDED_HOST = env('USE_X_FORWARDED_HOST', False)

# Do we allow public registration?
ALLOW_PUBLIC_REGISTRATION = env('ALLOW_PUBLIC_REGISTRATION', False)
# List of projects that a new user can be assign to as a custodian.
# If empty a new user won't be assigned to any project.
ALLOWED_PUBLIC_REGISTRATION_PROJECTS = env('ALLOWED_PUBLIC_REGISTRATION_PROJECTS', [])
