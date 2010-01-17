from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    #(r'^tagcloud/(?P<url>.+)/$', 'ucloud.tagcloud.views.handler'),
    (r'^tagcloud/$', 'lenx.tagcloud.views.handler'),
    (r'^ucloud/$', 'lenx.tagcloud.views.handler'),
    (r'^pippi/$', 'lenx.pippy.views.pippi'),
    (r'^xpippi/$', 'lenx.pippy.views.xpippi'),
)
