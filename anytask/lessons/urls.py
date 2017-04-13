from django.conf.urls import patterns, url

urlpatterns = patterns('lessons.views',
    url(r'^create/(?P<course_id>\d+)$', 'schedule_create_page'),
    url(r'^edit/(?P<lesson_id>\d+)$', 'schedule_edit_page'),
)