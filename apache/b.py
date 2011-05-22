import bjoern
import os, sys
import django.core.handlers.wsgi
sys.path.append(os.path.dirname(__file__)+'/..') 

os.environ['DJANGO_SETTINGS_MODULE'] = 'lenx.settings'
application = django.core.handlers.wsgi.WSGIHandler()
bjoern.run(application,'127.0.0.1',8040)
