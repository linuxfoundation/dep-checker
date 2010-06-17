from django.conf.urls.defaults import *
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^linkage/$', 'compliance.linkage.views.test'),
    (r'^linkage/test/$', 'compliance.linkage.views.test'),
    (r'^linkage/about/$', 'compliance.linkage.views.about'),
    (r'^linkage/authors/$', 'compliance.linkage.views.authors'),
    (r'^linkage/changelog/$', 'compliance.linkage.views.changelog'),
    (r'^linkage/license/$', 'compliance.linkage.views.license'),
    (r'^linkage/documentation/$', 'compliance.linkage.views.documentation'),
    (r'^linkage/setup/$', 'compliance.linkage.views.setup'),
    (r'^linkage/contributing/$', 'compliance.linkage.views.contributing'),
    (r'^linkage/results/$', 'compliance.linkage.views.results'),
    (r'^linkage/(?P<test_id>\d+)/detail/$', 'compliance.linkage.views.detail'),
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
	            {'document_root':  settings.STATIC_DOC_ROOT}),
    (r'^admin/', include(admin.site.urls)),
)
