from django.urls import re_path

import issues.views as views

urlpatterns = [
    re_path(r'^(?P<issue_id>\d+)$', views.issue_page, name="issues.views.issue_page"),
    re_path(r'^get_or_create/(?P<task_id>\d+)/(?P<student_id>\d+)$', views.get_or_create,
        name="issues.views.get_or_create"),
    re_path(r'^upload/$', views.upload, name='jfu_upload'),
    re_path(r'^delete/(?P<pk>\d+)$', views.upload_delete, name='jfu_delete'),
]
