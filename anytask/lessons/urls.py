from django.conf.urls import url
import lessons.views

urlpatterns = (
    url(r'^create/(?P<course_id>\d+)$', lessons.views.schedule_create_page,
        name="lessons.views.schedule_create_page"),
    url(r'^edit/(?P<lesson_id>\d+)$', lessons.views.schedule_edit_page,
        name="lessons.views.schedule_edit_page"),
)
