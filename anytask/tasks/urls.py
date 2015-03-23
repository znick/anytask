from django.conf.urls import patterns, url

urlpatterns = patterns('tasks.views',
    url(r'^popup/(?P<task_id>\d+)$', 'get_task_text_popup'),
    url(r'^update_status_check$', 'update_status_check'),
    url(r'^ajax_get_review_data/(?P<task_id>\d+)/(?P<student_id>\d+)$', 'ajax_get_review_data', name='ajax_get_review_data'),  
    url(r'^ajax_get_status_check/(?P<task_id>\d+)/(?P<student_id>\d+)$', 'ajax_get_status_check', name='ajax_get_status_check_data'),  
    url(r'^ajax_get_teacher/(?P<task_id>\d+)/(?P<student_id>\d+)$', 'ajax_get_teacher', name='ajax_get_teacher'),  
    url(r'^ajax_set_teacher/(?P<task_id>\d+)/(?P<student_id>\d+)/(?P<teacher_id>\d+)$', 'ajax_set_teacher', name='ajax_set_teacher'),  
    url(r'^ajax_delete_teacher/(?P<task_id>\d+)/(?P<student_id>\d+)$', 'ajax_delete_teacher', name='ajax_delete_teacher'),  
    url(r'^ajax_predict_status/(?P<task_id>\d+)/(?P<student_id>\d+)/(?P<score>\d+(?:\.\d+)?)$', 'ajax_predict_status', name='ajax_predict_status'),  
)
