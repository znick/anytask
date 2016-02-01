from django.conf.urls import patterns, url

urlpatterns = patterns('schools.views',
    url(r'^(?P<school_link>\d+)$', 'school_page'),

)
