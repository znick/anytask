from django.conf.urls import url
import invites.views

urlpatterns = [
    url(r'^generate_invites/$', invites.views.generate_invites,
        name="invites.views.generate_invites"),
]
