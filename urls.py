from django.conf.urls.defaults import *
from django.conf import settings
import view.views as view

urlpatterns = patterns('',
    (r'^tagcloud$', 'lenx.tagcloud.views.handler'),
    (r'^xpippi$', view.xpippiFormView),
    (r'^xpippi/(?P<doc>.+)', view.xpippi),
    (r'^all$', view.listDocs),
    (r'^view$', view.viewPippiDoc),
    (r'^view/(?P<cutoff>\d+)/(?P<doc>.+)/$', view.viewPippiDoc),
    (r'^view/(?P<doc>.+)/$', view.viewPippiDoc),
)
