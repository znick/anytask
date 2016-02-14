from django.conf.urls import patterns, url

urlpatterns = patterns('easy_ci.views',
    url(r'^(?P<student_id>\d+)/(?P<task_id>\d+)/submit$', 'task_taken_submit'),
    url(r'^(?P<student_id>\d+)/(?P<task_id>\d+)$', 'task_taken_view'),
    url(r'^file/(?P<easy_ci_task_id>\d+)$', 'check_task_view'),
)
