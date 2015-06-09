from django.conf.urls import patterns, url

urlpatterns = patterns('issues.views',
    url(r'^(?P<issue_id>\d+)$', 'issue_page'),
    url(r'^get_or_create/(?P<task_id>\d+)/(?P<student_id>\d+)$', 'get_or_create'),
    url(r'^event/(?P<event_id>\d+)$', 'upload_to_rb'),

)
