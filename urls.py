from django.conf.urls.defaults import *
from django.conf import settings
import view.views as view

urlpatterns = patterns('',
    (r'^$', view.index),
    (r'^tagcloud$', 'lenx.tagcloud.views.handler'),
    (r'^xpippi$', view.xpippiFormView),
    (r'^xpippi/(?P<doc>.+)', view.xpippi),
    (r'^all$', view.listDocs),
    (r'^stats$', view.stats),
    (r'^view$', view.viewPippiDoc),
    (r'^view/(?P<cutoff>\d+)/(?P<doc>.+)/$', view.viewPippiDoc),
    (r'^view/(?P<doc>.+)/$', view.viewPippiDoc),
    (r'^doc/(?P<doc>.+)$', view.docView),
)

if settings.DEV_SERVER:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_PATH}),
    )
