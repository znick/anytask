from django.conf.urls import patterns, url

urlpatterns = patterns('invites.views',
    url(r'^generate_invites/$', 'generate_invites'),
)