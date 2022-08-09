"""
WSGI config for biosys project.
It exposes the WSGI callable as a module-level variable named ``application``.
"""
import confy
import os
from pathlib2 import Path

d = Path(__file__).resolve().parents[1]
dot_env = os.path.join(str(d), '.env')
if os.path.exists(dot_env):
    confy.read_environment_file(dot_env)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biosys.settings')
from django.core.wsgi import get_wsgi_application
from dj_static import Cling, MediaCling

application = Cling(MediaCling(get_wsgi_application()))
