from django.urls import re_path
import lessons.views

urlpatterns = (
    re_path(r'^create/(?P<course_id>\d+)$', lessons.views.schedule_create_page,
        name="lessons.views.schedule_create_page"),
    re_path(r'^edit/(?P<lesson_id>\d+)$', lessons.views.schedule_edit_page,
        name="lessons.views.schedule_edit_page"),
)
