from django.conf.urls import patterns, url
from courses.pythontask import get_task, cancel_task
import courses.views

urlpatterns = [
    url(r'^(?P<course_id>\d+)$', courses.views.course_page, name='courses-views-course_page'),
    url(r'^(?P<course_id>\d+)/seminar/(?P<task_id>\d+)$', courses.views.seminar_page),
    url(r'^(?P<course_id>\d+)/queue$', courses.views.queue_page),
    url(r'^(?P<course_id>\d+)/gradebook/$', courses.views.gradebook),
    url(r'^(?P<course_id>\d+)/gradebook/seminar/(?P<task_id>\d+)/$', courses.views.gradebook),
    url(r'^(?P<course_id>\d+)/gradebook/group/(?P<group_id>\d+)/$', courses.views.gradebook),
    url(r'^(?P<course_id>\d+)/gradebook/seminar/(?P<task_id>\d+)/group/(?P<group_id>\d+)$', courses.views.gradebook),
    url(r'^year/(?P<year>\d+)', courses.views.courses_list),
    url(r'^edit_course_information', courses.views.edit_course_information),
    url(r'^set_spectial_course_attend', courses.views.set_spectial_course_attend),
    url(r'^(?P<course_id>\d+)/settings$', courses.views.course_settings),
    url(r'^change_visibility_hidden_tasks$', courses.views.change_visibility_hidden_tasks),
    url(r'^change_visibility_academ_users$', courses.views.change_visibility_academ_users),
    url(r'^set_course_mark$', courses.views.set_course_mark),
    url(r'^set_task_mark$', courses.views.set_task_mark),
    url(r'^change_table_tasks_pos', courses.views.change_table_tasks_pos),
    url(r'^ajax_update_contest_tasks/$', courses.views.ajax_update_contest_tasks),
    url(r'^ajax_rejudge_contest_tasks/$', courses.views.ajax_rejudge_contest_tasks),
    url(r'^pythontask/get_task/(?P<course_id>\d+)/(?P<task_id>\d+)$', get_task),
    url(r'^pythontask/cancel_task/(?P<course_id>\d+)/(?P<task_id>\d+)$', cancel_task),
    url(r'^(?P<course_id>\d+)/attendance$', courses.views.attendance_page),
    url(r'^(?P<course_id>\d+)/attendance/group/(?P<group_id>\d+)/$', courses.views.attendance_page),
    url(r'^lesson_visited$', courses.views.lesson_visited),
    url(r'^lesson_delete$', courses.views.lesson_delete),
    url(r'^(?P<course_id>\d+)/statistic$', courses.views.view_statistic),
    url(r'^ajax_get_queue$', courses.views.ajax_get_queue),
]
