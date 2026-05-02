from django.urls import re_path
from schools import views

urlpatterns = [
    re_path(r'^(?P<school_link>\w+)$', views.school_page,
        name="schools.views.school_page"),
    re_path(r'^(?P<school_link>\w+)/archive$', views.archive_page,
        name="schools.views.archive_page")
]
