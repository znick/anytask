from django.conf.urls import patterns, url


urlpatterns = patterns('courses.views',
    url(r'^(?P<course_id>\d+)$', 'course_page'),
    url(r'^(?P<course_id>\d+)/seminar/(?P<task_id>\d+)$', 'seminar_page'),
    url(r'^(?P<course_id>\d+)/queue$', 'queue_page'),
    url(r'^(?P<course_id>\d+)/gradebook/$', 'gradebook'),
    url(r'^(?P<course_id>\d+)/gradebook/seminar/(?P<task_id>\d+)/$', 'gradebook'),
    url(r'^(?P<course_id>\d+)/gradebook/group/(?P<group_id>\d+)/$', 'gradebook'),
    url(r'^(?P<course_id>\d+)/gradebook/(?P<task_id>\d+)/(?P<group_id>\d+)$', 'gradebook'),
    url(r'^year/(?P<year>\d+)', 'courses_list'),
    url(r'^edit_course_information', 'edit_course_information'),
    url(r'^set_spectial_course_attend', 'set_spectial_course_attend'),
    url(r'^(?P<course_id>\d+)/settings$', 'course_settings'),
    url(r'^change_visibility_hidden_tasks$', 'change_visibility_hidden_tasks'),
    url(r'^change_visibility_academ_users$', 'change_visibility_academ_users'),
    url(r'^set_course_mark$', 'set_course_mark'),
    url(r'^set_task_mark$', 'set_task_mark'),
    url(r'^change_table_tasks_pos', 'change_table_tasks_pos'),
    url(r'^ajax_update_contest_tasks/$', 'ajax_update_contest_tasks'),
    url(r'^ajax_rejudge_contest_tasks/$', 'ajax_rejudge_contest_tasks'),
)
