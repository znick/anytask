from django.conf.urls import patterns, url

urlpatterns = patterns('issues.views',
    url(r'^(?P<issue_id>\d+)$', 'issue_page'),
    url(r'^get_or_create/(?P<task_id>\d+)/(?P<student_id>\d+)$', 'get_or_create'),
    url(r'^update/(?P<review_id>\d+)$', 'message_from_rb'),

)
