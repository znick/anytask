from django.conf.urls import patterns, url

urlpatterns = patterns('admission.views',
                       url(r'^register$', 'register'),
                       url(r'^activate/(?P<activation_key>\w+)/', 'activate'),
                       )
