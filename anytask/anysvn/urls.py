from django.conf.urls import patterns, url
from anysvn.views import SvnAccesss

urlpatterns = patterns(
    'anysvn.views',
    url(r'^access/$', SvnAccesss.as_view(),
        name="anysvn.views.SvnAccesss.as_view"),
)
