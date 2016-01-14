"""
Django settings for biosys project.
"""
from confy import database
import os
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root = lambda *x: os.path.join(BASE_DIR, *x)
sys.path.insert(0, root('apps'))  # Add the apps directory into the path


# Security settings
SECRET_KEY = os.environ['SECRET_KEY'] if os.environ.get('SECRET_KEY', False) else 'foo'
DEBUG = True if os.environ.get('DEBUG', False) == 'True' else False
CSRF_COOKIE_SECURE = True if os.environ.get('CSRF_COOKIE_SECURE', False) == 'True' else False
SESSION_COOKIE_SECURE = True if os.environ.get('SESSION_COOKIE_SECURE', False) == 'True' else False
if not DEBUG:
    # Localhost, UAT and Production hosts
    ALLOWED_HOSTS = [
        'localhost',
        '127.0.0.1',
        'biosys.dpaw.wa.gov.au',
        'biosys.dpaw.wa.gov.au.',
        'biosys-uat.dpaw.wa.gov.au',
        'biosys-uat.dpaw.wa.gov.au.',
    ]


# Application definition
# The variables below are added to all responses in biosys/context_processors.py
SITE_TITLE = 'BioSys - WA Biological Survey Database'
APPLICATION_VERSION_NO = '1.0'

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
    # Third-party apps.
    'django_extensions',
    'envelope',
    'reversion',
    'tastypie',
    'webtemplate_dpaw',
    'django_wsgiserver',
)

PROJECT_APPS = (
    'main',
    'species',
    'vegetation',
    'animals',
    'upload',
    'download',
    'publish',
)

INSTALLED_APPS += PROJECT_APPS

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'reversion.middleware.RevisionMiddleware',
    'dpaw_utils.middleware.SSOLoginMiddleware',
)

ROOT_URLCONF = 'biosys.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [root('templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.core.context_processors.debug",
                "django.core.context_processors.i18n",
                "django.core.context_processors.media",
                "django.core.context_processors.static",
                "django.core.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "django.core.context_processors.request",
                "biosys.context_processors.standard",
            ],
        },
    },
]

WSGI_APPLICATION = 'biosys.wsgi.application'


# Database
DATABASES = {'default': database.config()}

# Internationalization
LANGUAGE_CODE = 'en-au'
TIME_ZONE = 'Australia/Perth'
USE_I18N = True
USE_L10N = True
USE_TZ = True
# Set the formats that will be displayed in date fields
# If USE_L10N == True, then locale-dictated format has higher precedence.
DATE_FORMAT = '%d/%m/%Y'      # O5/10/2006
# Set the formats that will be accepted in date input fields
DATE_INPUT_FORMATS = (
    '%d/%m/%Y',             # '25/10/2006'
    '%Y-%m-%d',             # '2006-10-25'
    '%Y_%m_%d',             # '2006_10_25'
)


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_URL = '/static/'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = root('..', 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = 'static'

# Additional locations of static files
STATICFILES_DIRS = (
    root('static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'


# Logging settings
LOG_FOLDER = root('..', 'log')
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
            'level': 'WARNING',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_FOLDER, 'biosys.log'),
            'when': 'midnight',
            'backupCount': 2,
            'formatter': 'default',
        },
        'console': {
            'level': 'WARNING',
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
            'propagate': True,
        },
    }
}


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

# .local.py overrides all the common settings.
try:
    from .local import *
except ImportError:
    pass


# if len(sys.argv) > 1 and 'test' in sys.argv[1]:
#     from .testing import *

# django-tastypie settings
TASTYPIE_ALLOW_MISSING_SLASH = True
TASTYPIE_DATETIME_FORMATTING = 'iso-8601-strict'
TASTYPIE_DEFAULT_FORMATS = ['json', 'html']
API_LIMIT_PER_PAGE = 0


# Grappelli settings
GRAPPELLI_ADMIN_TITLE = SITE_TITLE + ' administration'

# envelop extensions
ENVELOPE_EMAIL_RECIPIENTS = ['biosys@DPaW.wa.gov.au']
ENVELOPE_USE_HTML_EMAIL = False

EMAIL_HOST = 'alerts.corporateict.domain'
EMAIL_PORT = 25
