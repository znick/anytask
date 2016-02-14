from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.views.generic.simple import direct_to_template



# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'anytask.views.home', name='home'),
    # url(r'^anytask/', include('anytask.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^course/', include('cources.urls')),
    url(r'^task/', include('tasks.urls')),
    url(r'^user/', include('users.urls')),
    url(r'^invites/', include('invites.urls')),
    url(r'^anysvn/', include('anysvn.urls')),
    url(r'^accounts/profile/(?P<username>.*)/(?P<year>\d+)', 'users.views.profile'),
    url(r'^accounts/profile/(?P<username>.*)', 'users.views.profile'),
    url(r'^accounts/profile', 'users.views.profile'),
    url(r'^accounts/', include('registration.backends.default_with_names.urls')),
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    #url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    url(r'^about$', direct_to_template, {'template' : 'about.html'}),
    url(r'^easy_ci/', include('easy_ci.urls')),
    url(r'^$', 'index.views.index'),
)
