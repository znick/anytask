from django.urls import re_path
import invites.views

urlpatterns = [
    re_path(r'^generate_invites/$', invites.views.generate_invites,
        name="invites.views.generate_invites"),
]
