from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication

from notes.handlers import AnnotationHandler, SearchHandler

auth = HttpBasicAuthentication(realm="Annotator")
ad = { 'authentication': auth }

annotation_resource = Resource(handler=AnnotationHandler, **ad)
search_resource = Resource(handler=SearchHandler)

urlpatterns = patterns('',
    url(r'^$', annotation_resource),
    url(r'^search$', search_resource),
    url(r'^(?P<id>.*)$', annotation_resource),
)
