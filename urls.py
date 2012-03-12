from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
     url(r'^$', 'regalness.views.index', name='home'),
     url(r'^experimental/$', 'regalness.views.experimental', name='experimental'),
     url(r'^register/$', 'regalness.views.register', name='register'),
     url(r'^login/$', 'regalness.views.login', name='login'),
     url(r'^deets/$', 'regalness.views.order_details', name='order_details'),
     url(r'^contact/$', 'regalness.views.contact', name='contact'),
     url(r'^s/(?P<option>[\w-]+)/(?P<quantity>\d+)/(?P<token>[\w-]+)/$', 'regalness.views.order_submit', name='order_submit'),
    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('',
    (r'^public/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT }),
)
