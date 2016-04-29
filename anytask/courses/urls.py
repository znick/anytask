from django.conf.urls import patterns, url


urlpatterns = patterns('courses.views',
    url(r'^(?P<course_id>\d+)$', 'course_page'),
    url(r'^(?P<course_id>\d+)/queue$', 'queue_page'),
    url(r'^edit_task', 'edit_task'),
    url(r'^add_task', 'add_task'),
    url(r'^year/(?P<year>\d+)', 'courses_list'),
    url(r'^edit_course_information', 'edit_course_information'),
    url(r'^set_spectial_course_attend', 'set_spectial_course_attend'),
    url(r'^(?P<course_id>\d+)/settings$', 'course_settings'),
    url(r'^get_contest_problems', 'get_contest_problems'),
    url(r'^change_visibility_hidden_tasks$', 'change_visibility_hidden_tasks'),
)
