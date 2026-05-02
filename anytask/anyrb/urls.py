from django.urls import re_path
import anyrb.views

urlpatterns = [
    re_path(r'^update/(?P<review_id>\d+)$', anyrb.views.message_from_rb,
        name="anyrb.views.message_from_rb"),
]
