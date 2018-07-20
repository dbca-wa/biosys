"""
WSGI config for biosys project.
It exposes the WSGI callable as a module-level variable named ``application``.
"""
from __future__ import absolute_import, unicode_literals, print_function, division

import os
from confy import read_environment_file, env
from django.core.wsgi import get_wsgi_application
from dj_static import Cling, MediaCling

env_file = env('ENV_FILE')

if env_file is not None:
    read_environment_file(env('ENV_FILE'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "biosys.settings")
application = Cling(MediaCling(get_wsgi_application()))
