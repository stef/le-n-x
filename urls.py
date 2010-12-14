from django.conf.urls.defaults import *
from django.conf import settings
import view.views as view

urlpatterns = patterns('',
    (r'^$', view.index),
    (r'^tinymce/', include('tinymce.urls')),
    (r'^tagcloud$', 'lenx.tagcloud.views.handler'),
    (r'^all$', view.listDocs),
    (r'^stats$', view.stats),
    (r'^create$', view.createDoc),
    (r'^frags$', view.frags),
    (r'^pippies$', view.pippies),
    (r'^pippi/(?P<refdoc>.+)$', view.pippi),
    (r'^meta/(?P<doc>.+)$', view.metaView),
    (r'^job$', view.job),
    (r'^doc/(?P<doc>.+)$', view.docView),
    (r'^toggle_star/(?P<id>.+)$', view.toggle_star),
    (r'^starred$', view.starred),
    (r'^search$', view.search),
)

if settings.DEV_SERVER:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_PATH}),
    )
