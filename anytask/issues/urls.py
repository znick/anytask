from django.conf.urls import patterns, url

urlpatterns = patterns('issues.views',
    url(r'^(?P<issue_id>\d+)$', 'issue_page'),
    url(r'^get_or_create/(?P<task_id>\d+)/(?P<student_id>\d+)$', 'get_or_create'),
    url( r'^(?P<issue_id>\d+)/upload/$', views.upload, name = 'jfu_upload' ),
    url( r'^delete/(?P<pk>\d+)$', views.upload_delete, name = 'jfu_delete' ),
)
