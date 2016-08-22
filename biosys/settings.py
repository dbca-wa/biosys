"""
Django settings for biosys project.
"""
from confy import env, database
import os
import sys
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
SECRET_KEY = env('SECRET_KEY')
CSRF_COOKIE_SECURE = env('CSRF_COOKIE_SECURE', False)
SESSION_COOKIE_SECURE = env('SESSION_COOKIE_SECURE', False)
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
APPLICATION_VERSION_NO = '2.0.0'

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
    'bootstrap3',
    'timezone_field'
)

PROJECT_APPS = (
    'main',
    'species',
    'publish',


    # legacy apps
    'vegetation',
    'animals',
    'upload',
    'download',
    'old_publish',
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
    'django.middleware.gzip.GZipMiddleware',
    'reversion.middleware.RevisionMiddleware',
    'dpaw_utils.middleware.SSOLoginMiddleware',
)

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
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
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

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

BOOTSTRAP3 = {
    'jquery_url': '//static.dpaw.wa.gov.au/static/libs/jquery/2.2.1/jquery.min.js',
    'base_url': '//static.dpaw.wa.gov.au/static/libs/twitter-bootstrap/3.3.6/',
    'css_url': None,
    'theme_url': None,
    'javascript_url': None,
    'javascript_in_head': False,
    'include_jquery': False,
    'required_css_class': 'required-form-field',
    'set_placeholder': False,
}

HERBIE_SPECIES_WFS_URL = env('HERBIE_SPECIES_WFS_URL',
                             'https://kmi.dpaw.wa.gov.au/geoserver/ows?service=wfs&version=1.1.0&'
                             'request=GetFeature&typeNames=public:herbie_hbvspecies_public&outputFormat=application/json')

# Logging settings
# Ensure that the logs directory exists:
LOG_FOLDER = os.path.join(BASE_DIR, 'logs')
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
        'import_lci': {
            'level': env('LOG_LCI_LEVEL', 'ERROR'),
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_FOLDER, 'import_lci.log'),
            'mode': 'w',
            'formatter': 'import_legacy',
        }
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
        },
        'import_lci': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)


# django-tastypie settings
TASTYPIE_ALLOW_MISSING_SLASH = True
TASTYPIE_DATETIME_FORMATTING = 'iso-8601-strict'
TASTYPIE_DEFAULT_FORMATS = ['json']
API_LIMIT_PER_PAGE = 0

# Grappelli settings
GRAPPELLI_ADMIN_TITLE = SITE_TITLE + ' administration'

# envelop extensions
ENVELOPE_EMAIL_RECIPIENTS = ['biosys@DPaW.wa.gov.au']
ENVELOPE_USE_HTML_EMAIL = False

# Email settings
EMAIL_HOST = env('EMAIL_HOST', 'email.host')
EMAIL_PORT = env('EMAIL_PORT', 25)
