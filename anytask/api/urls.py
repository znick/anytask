from django.conf.urls import patterns, url

urlpatterns = patterns('api.views',
                       url(r'^v1/course/(?P<course_id>\d+)/statuses$', 'get_issue_statuses'),
                       url(r'^v1/course/(?P<course_id>\d+)/issues$', 'get_issues'),
                       url(r'^v1/issue/(?P<issue_id>\d+)/add_comment$', 'add_comment'),
                       url(r'^v1/issue/(?P<issue_id>\d+)$', 'get_or_post_issue'),
                       url(r'^v1/check_user$', 'check_user'),
                       )
