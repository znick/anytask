from django.conf.urls import patterns, url


urlpatterns = patterns('courses.views',
    url(r'^(?P<course_id>\d+)$', 'course_page'),
    url(r'^(?P<course_id>\d+)/queue$', 'queue_page'),
    url(r'^year/(?P<year>\d+)', 'courses_list'),
    url(r'^edit_course_information', 'edit_course_information'),
    url(r'^set_spectial_course_attend', 'set_spectial_course_attend'),
    url(r'^(?P<course_id>\d+)/settings$', 'course_settings'),
    url(r'^change_visibility_hidden_tasks$', 'change_visibility_hidden_tasks'),
    url(r'^set_course_mark$', 'set_course_mark'),
    url(r'^set_task_mark$', 'set_task_mark'),
)
