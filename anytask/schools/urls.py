from django.conf.urls import url
from schools import views

urlpatterns = [
    url(r'^(?P<school_link>\w+)$', views.school_page,
        name="schools.views.school_page"),
    url(r'^(?P<school_link>\w+)/archive$', views.archive_page,
        name="schools.views.archive_page")
]
