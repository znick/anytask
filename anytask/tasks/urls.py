from django.conf.urls import patterns, url

urlpatterns = patterns('tasks.views',
    url(r'^popup/(?P<task_id>\d+)$', 'get_task_text_popup'),
)
