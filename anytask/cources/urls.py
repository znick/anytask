from django.conf.urls import patterns, url

from cources.views import SubmitReview, SubmitReviewForm

urlpatterns = patterns('cources.views',
    url(r'^(?P<cource_id>\d+)$', 'tasks_list'),
    url(r'^get_task/(?P<cource_id>\d+)/(?P<task_id>\d+)$', 'get_task'),
    url(r'^cancel_task/(?P<cource_id>\d+)/(?P<task_id>\d+)$', 'cancel_task'),
    url(r'^score_task', 'score_task'),
    url(r'^edit_cource_information', 'edit_cource_information'),
    url(r'^edit_task', 'edit_task'),
    url(r'^add_task', 'add_task'),
    url(r'^year/(?P<year>\d+)', 'cources_list'),
    url(r'^statistics/(?P<cource_id>\d+)', 'cource_statistics'),
    url(r'^tasks_description/(?P<cource_id>\d+)', 'tasks_description'),
    url(r'^set_spectial_course_attend', 'set_spectial_course_attend'),
    url(r'^submit_review_form/(?P<task_id>\d+)/(?P<svn_path>.*)', SubmitReviewForm.as_view()),
    url(r'^submit_review/(?P<task_id>\d+)$', SubmitReview.as_view(), name='submit_review'),
)
