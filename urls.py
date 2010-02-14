from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^tagcloud/$', 'lenx.tagcloud.views.handler'),
    (r'^pippi/$', 'lenx.pippy.views.pippi'),
    (r'^stats/$', 'lenx.stats.views.stats'),
    (r'^xpippi/$', 'lenx.view.views.xpippi'),
    (r'^view/$', 'lenx.view.views.viewPippiDoc'),
    (r'^view/(?P<cutoff>\d+)/(?P<doc>.+)/$', 'lenx.view.views.viewPippiDoc'),
    (r'^view/(?P<doc>.+)/$', 'lenx.view.views.viewPippiDoc'),
)
