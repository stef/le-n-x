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
    (r'^import$', view.importDoc),
    (r'^frags$', view.frags),
    (r'^pippies$', view.pippies),
    (r'^pippi/(?P<refdoc>.+)$', view.pippi),
    (r'^job$', view.job),
    (r'^doc/(?P<doc>.+)$', view.docView),
    (r'^search$', view.search),
)

if settings.DEV_SERVER:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_PATH}),
    )
