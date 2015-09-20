from django.conf.urls import patterns, url

from courses.views import SubmitReview, SubmitReviewForm
from filemanager import path_end

urlpatterns = patterns('courses.views',
    url(r'^(?P<course_id>\d+)$', 'course_page'),
    url(r'^(?P<course_id>\d+)/queue$', 'queue_page'),
    url(r'^get_task/(?P<course_id>\d+)/(?P<task_id>\d+)$', 'get_task'),
    url(r'^cancel_task/(?P<course_id>\d+)/(?P<task_id>\d+)$', 'cancel_task'),
    url(r'^score_task', 'score_task'),
    url(r'^edit_course_information', 'edit_course_information'),
    url(r'^edit_task', 'edit_task'),
    url(r'^add_task', 'add_task'),
    url(r'^year/(?P<year>\d+)', 'courses_list'),
    url(r'^statistics/(?P<course_id>\d+)', 'course_statistics'),
    url(r'^tasks_description/(?P<course_id>\d+)', 'tasks_description'),
    url(r'^set_spectial_course_attend', 'set_spectial_course_attend'),
    url(r'^submit_review_form/(?P<task_id>\d+)/(?P<svn_path>.*)', SubmitReviewForm.as_view()),
    url(r'^submit_pdf_gr_form/(?P<task_id>\d+)', 'submit_pdf_gr_form', name='submit_pdf_gr_form'),
    url(r'^submit_review/(?P<task_id>\d+)$', SubmitReview.as_view(), name='submit_review'),
    url(r'^queue_tasks_to_check/(?P<course_id>\d+)', 'queue_tasks_to_check'),
    url(r'^ajax_get_transcript/(?P<course_id>\d+)', 'ajax_get_transcript'),
    url(r'^tasks_list/(?P<course_id>\d+)', 'tasks_list'),
    url(r'^(?P<course_id>\d+)/settings$', 'course_settings'),
    url(r'^(?P<course_id>\d+)/data/$'+path_end,'filemanager'),
)
