from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
     url(r'^$', 'regal.orders.views.index', name='home'),
     url(r'^experimental/$', 'regal.orders.views.experimental', name='experimental'),
     url(r'^register/$', 'regal.orders.views.register', name='register'),
     url(r'^login/$', 'regal.orders.views.login', name='login'),
     url(r'^deets/$', 'regal.orders.views.order_details', name='order_details'),
     url(r'^contact/$', 'regal.orders.views.contact', name='contact'),
     url(r'^review/$', 'regal.orders.views.review', name='review'),
     url(r'^s/(?P<option>[\w-]+)/(?P<quantity>\d+)/(?P<token>[\w-]+)/$', 'regal.orders.views.order_submit', name='order_submit'),
    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns('',
    (r'^public/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT }),
)
