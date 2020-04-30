from django.conf.urls import patterns, url
import tasks.views

urlpatterns = [
    url(r'^create/(?P<course_id>\d+)$', tasks.views.task_create_page),
    url(r'^import/(?P<course_id>\d+)$', tasks.views.task_import_page),
    url(r'^contest_import/(?P<course_id>\d+)$', tasks.views.contest_import_page),
    url(r'^edit/(?P<task_id>\d+)$', tasks.views.task_edit_page),
    url(r'^get_contest_problems', tasks.views.get_contest_problems),
    url(r'^contest_task_import', tasks.views.contest_task_import),
    url(r'^popup/(?P<task_id>\d+)$', tasks.views.get_task_text_popup),
    url(r'^validate/nb_assignment_name', tasks.views.validate_nb_assignment_name),
]
