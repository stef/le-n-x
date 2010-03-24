import os, sys

apache_configuration= os.path.dirname(__file__)
project = os.path.dirname(apache_configuration)
workspace = os.path.dirname(project)
sys.path.append(workspace) 

os.environ['DJANGO_SETTINGS_MODULE'] = 'lenx.settings'
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

# Apache sites-enabled config:
#
# WSGIScriptAlias /pippi_url "/path/to/your/le-n-x/apache/django.wsgi"
# Alias /pippi_url/media "/path/to/your/le-n-x/media"
# <Directory "/path/to/your/le-n-x">
#     Options FollowSymLinks
#     AllowOverride All
# </Directory>
