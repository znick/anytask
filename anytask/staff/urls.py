from django.conf.urls import patterns, url

urlpatterns = patterns('staff.views',
    url(r'^$', 'staff_page'),
)
