from django.urls import re_path
from anysvn.views import SvnAccesss

urlpatterns = [
    re_path(r'^access/$', SvnAccesss.as_view(),
        name="anysvn.views.SvnAccesss.as_view"),
]
