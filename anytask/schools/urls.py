from django.conf.urls import patterns, url

urlpatterns = patterns('schools.views',
    url(r'^(?P<school_link>\w+)$', 'school_page'),

)
