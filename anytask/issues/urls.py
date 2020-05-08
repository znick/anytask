from django.conf.urls import url

import issues.views as views

urlpatterns = [
    url(r'^(?P<issue_id>\d+)$', views.issue_page, name="issues.views.issue_page"),
    url(r'^get_or_create/(?P<task_id>\d+)/(?P<student_id>\d+)$', views.get_or_create,
        name="issues.views.get_or_create"),
    url(r'^upload/$', views.upload, name='jfu_upload'),
    url(r'^delete/(?P<pk>\d+)$', views.upload_delete, name='jfu_delete'),
]
