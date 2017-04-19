from django.conf.urls import patterns, url

urlpatterns = patterns('tasks.views',
    url(r'^create/(?P<course_id>\d+)$', 'task_create_page'),
    url(r'^import/(?P<course_id>\d+)$', 'task_import_page'),
    url(r'^contest_import/(?P<course_id>\d+)$', 'contest_import_page'),
    url(r'^edit/(?P<task_id>\d+)$', 'task_edit_page'),
    url(r'^get_contest_problems', 'get_contest_problems'),
    url(r'^contest_task_import', 'contest_task_import'),
    url(r'^popup/(?P<task_id>\d+)$', 'get_task_text_popup'),
)
