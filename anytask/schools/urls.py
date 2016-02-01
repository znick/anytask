from django.conf.urls import patterns, url

urlpatterns = patterns('school.views',
    url(r'^(?P<school_id>\d+)$', 'school_page'),

)
