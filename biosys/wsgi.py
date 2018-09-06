"""
WSGI config for biosys project.
It exposes the WSGI callable as a module-level variable named ``application``.
"""
from __future__ import absolute_import, unicode_literals, print_function, division

import os
import logging

import confy
from django.core.wsgi import get_wsgi_application
from dj_static import Cling, MediaCling

logger = logging.getLogger(__name__)

if confy.env('ENV_FILE') is not None:
    confy.read_environment_file(confy.env('ENV_FILE'))
else:
    try:
        confy.read_environment_file(".env")
    except:
        logger.info('.env file not found')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "biosys.settings")
application = Cling(MediaCling(get_wsgi_application()))
