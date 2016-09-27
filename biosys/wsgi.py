"""
WSGI config for biosys project.
It exposes the WSGI callable as a module-level variable named ``application``.
"""
from __future__ import absolute_import, unicode_literals, print_function, division

import os
import confy
from django.core.wsgi import get_wsgi_application
from dj_static import Cling, MediaCling

confy.read_environment_file('.env')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "biosys.settings")
application = Cling(MediaCling(get_wsgi_application()))
