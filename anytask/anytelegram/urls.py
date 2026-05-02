import anytelegram.views
from django.urls import re_path

urlpatterns = [
    re_path(r'^webhook/(?P<token>[0-9a-z\-]+)$', anytelegram.views.webhook,
        name='anytelegram.views.webhook')
]
