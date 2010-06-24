from django.conf.urls.defaults import *
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^linkage/$', 'compliance.linkage.views.test'),
    (r'^linkage/test/$', 'compliance.linkage.views.test'),
    (r'^linkage/dirlist/$', 'compliance.linkage.views.dirlist'),
    (r'^linkage/documentation/$', 'compliance.linkage.views.documentation'),
    (r'^linkage/results/$', 'compliance.linkage.views.results'),
    (r'^linkage/licenses\/$', 'compliance.linkage.views.licenses'),
    (r'^linkage/policy/$', 'compliance.linkage.views.policy'),
    (r'^linkage/(?P<test_id>\d+)/detail/$', 'compliance.linkage.views.detail'),
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
	            {'document_root':  settings.STATIC_DOC_ROOT}),
    (r'^admin/', include(admin.site.urls)),
)
