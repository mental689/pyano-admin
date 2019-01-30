import os, sys
sys.path.insert(0, os.path.abspath('..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'pyano_admin.settings'
import django
django.setup()
from vatic.models import Video
from django.conf import settings
import logging