from django.conf.urls.defaults import *
from django.conf import settings
import view.views as view

urlpatterns = patterns('',
    (r'^$', view.index),
    (r'^tinymce/', include('tinymce.urls')),
    (r'^tagcloud$', 'lenx.tagcloud.views.handler'),
    (r'^all$', view.listDocs),
    (r'^browse$', view.browseDocs),
    (r'^filter$', view.filterDocs),
    (r'^stats$', view.stats),
    (r'^create$', view.createDoc),
    (r'^frags$', view.frags),
    (r'^pippies$', view.pippies),
    (r'^pippi/(?P<refdoc>.+)$', view.pippi),
    (r'^meta/(?P<doc>.+)$', view.metaView),
    (r'^job$', view.job),
    (r'^jobs$', view.jobs),
    (r'^doc/(?P<doc>.+)$', view.docView),
    (r'^title/(?P<docid>.+)$', view.setTitle),
    (r'^delete/(?P<docid>.+)$', view.delete),
    (r'^toggle_star/(?P<id>.+)$', view.toggle_star),
    (r'^starred$', view.starred),
    (r'^search$', view.search),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page' : '/all'}),
    (r'^accounts/', include('registration.urls')),
    url(r'^annotations/', include('lenx.notes.urls')),
)

if settings.DEV_SERVER:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_PATH}),
    )
