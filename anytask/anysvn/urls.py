from django.conf.urls import url
from anysvn.views import SvnAccesss

urlpatterns = [
    url(r'^access/$', SvnAccesss.as_view(),
        name="anysvn.views.SvnAccesss.as_view"),
]
