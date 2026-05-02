import tasks.views
from django.urls import re_path

urlpatterns = [
    re_path(r'^create/(?P<course_id>\d+)$', tasks.views.task_create_page,
        name="tasks.views.task_create_page"),
    re_path(r'^import/(?P<course_id>\d+)$', tasks.views.task_import_page,
        name="tasks.views.task_import_page"),
    re_path(r'^contest_import/(?P<course_id>\d+)$', tasks.views.contest_import_page,
        name="tasks.views.contest_import_page"),
    re_path(r'^edit/(?P<task_id>\d+)$', tasks.views.task_edit_page,
        name="tasks.views.task_edit_page"),
    re_path(r'^get_contest_problems', tasks.views.get_contest_problems,
        name="tasks.views.get_contest_problems"),
    re_path(r'^contest_task_import', tasks.views.contest_task_import,
        name="tasks.views.contest_task_import"),
    re_path(r'^popup/(?P<task_id>\d+)$', tasks.views.get_task_text_popup,
        name="tasks.views.get_task_text_popup"),
    re_path(r'^validate/nb_assignment_name', tasks.views.validate_nb_assignment_name,
        name="tasks.views.validate_nb_assignment_name"),
]
