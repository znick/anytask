import command_tasks.views
from django.conf.urls import url

urlpatterns = [
    url(r'^create/(?P<course_id>\d+)$', command_tasks.views.task_create_page,
        name="command_tasks.views.task_create_page"),
    url(r'^edit/(?P<task_id>\d+)$', command_tasks.views.task_edit_page,
        name="command_tasks.views.task_edit_page"),
    url(r'^popup/(?P<task_id>\d+)$', command_tasks.views.get_task_text_popup,
        name="command_tasks.views.get_task_text_popup"),
    url(r'^validate/nb_assignment_name', command_tasks.views.validate_nb_assignment_name,
        name="command_tasks.views.validate_nb_assignment_name"),
]
