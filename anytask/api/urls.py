from django.conf.urls import patterns, url


urlpatterns = patterns('api.views',
                       url(r'^v1/api/course/(?P<course_id>\d+)/issue$', 'get_issues'),
)
