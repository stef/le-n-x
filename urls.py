from django.conf.urls.defaults import *
from brain.document import MatchDb
db=MatchDb()
db.load()

urlpatterns = patterns('',
    # Example:
    #(r'^tagcloud/(?P<url>.+)/$', 'ucloud.tagcloud.views.handler'),
    (r'^tagcloud/$', 'lenx.tagcloud.views.handler'),
    (r'^ucloud/$', 'lenx.tagcloud.views.handler'),
    (r'^pippi/$', 'lenx.pippy.views.pippi'),
    (r'^xpippi/$', 'lenx.pippy.views.xpippi'),
    (r'^stats/$', 'lenx.stats.views.stats'),
    (r'^view/$', 'lenx.view.views.viewPippiDoc',{'db': db}),
    (r'^view/(?P<cutoff>\d+)/(?P<doc>.+)/$', 'lenx.view.views.viewPippiDoc',{'db': db}),
    (r'^view/(?P<doc>.+)/$', 'lenx.view.views.viewPippiDoc',{'db': db}),
)
