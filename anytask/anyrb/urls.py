from django.conf.urls import url
import anyrb.views

urlpatterns = [
    url(r'^update/(?P<review_id>\d+)$', anyrb.views.message_from_rb,
        name="anyrb.views.message_from_rb"),
]
