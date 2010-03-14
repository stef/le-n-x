import os, sys
os.environ['DJANGO_SETTINGS_MODULE']='settings'
sys.path = [os.path.dirname(os.path.dirname(__file__))] + sys.path # add pythonpath to
import django.core.handlers.wsgi
_application = django.core.handlers.wsgi.WSGIHandler()
from django.conf import settings

def application(environ, start_response):
    if settings.ROOT_URL != '/':
        environ['SCRIPT_NAME'] = settings.ROOT_URL[:-1]
        # environ['PATH_INFO'] = environ['SCRIPT_NAME'] + environ['PATH_INFO']
    return _application(environ, start_response)


# Apache sites-enabled config:
#
# WSGIScriptAlias /pippi_url "/path/to/your/le-n-x/apache/django.wsgi"
# Alias /pippi_url/media "/path/to/your/le-n-x/media"
# <Directory "/path/to/your/le-n-x">
#     Options FollowSymLinks
#     AllowOverride All
# </Directory>
