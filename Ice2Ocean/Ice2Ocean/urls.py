"""
Definition of urls for Ice2Ocean.
"""


from datetime import datetime
from django.conf.urls import patterns, url, include
from django.contrib import admin
from django.http import HttpResponse
admin.autodiscover()
from app.forms import BootstrapAuthenticationForm
import app
import app.admincontrols as admincontrols


urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'app.views.home', name='home'),
    url(r'^contact$', 'app.views.contact', name='contact'),
    url(r'^about', 'app.views.about', name='about'),
    url(r'^restful','app.views.restful',name='restful'),

    # API
    url(r'^api/music','app.api.music'),
    url(r'^api/get-raster','app.api.getraster'),
    url(r'^api/get-info', 'app.api.getinfo'),
    url(r'^api/clear', 'app.api.clearservercache'),
    url(r'^api/list', 'app.api.listcache'),
    url(r'^api/get-vector','app.api.getvector'),
    url(r'^api/get-timeseries','app.api.gettimeseries'),
    url(r'^metadata/get-timeseries','app.api.gettimeseries_metadata'),

    # Login authentication
    url(r'^login/$',
        'django.contrib.auth.views.login',
        {
            'template_name': 'app/login.html',
            'authentication_form': BootstrapAuthenticationForm,
            'extra_context':
            {
                'title':'Log in',
                'year':datetime.now().year,
            }
        },
        name='login'),
    url(r'^logout$',
        'django.contrib.auth.views.logout',
        {
            'next_page': '/',
        },
        name='logout'),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Administrative settings for Ice2Ocean.
     url(r'^admin/settings/$', admin.site.admin_view(admincontrols.settings)),
    # Administrative settings for Ice2Ocean.
     url(r'^admin/cache/$', admin.site.admin_view(admincontrols.cachemon)),
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
