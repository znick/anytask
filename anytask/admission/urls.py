from django.conf.urls import patterns, url

urlpatterns = patterns('admission.views',
                       url(r'^ya_form_register$', 'register'),
                       url(r'^activate/(?P<activation_key>\w+)/', 'activate'),
                       url(r'^results/(?P<username>.*)/', 'contest_results_redirect'),
                       # url(r'^decline/(?P<activation_key>\w+)/', 'decline'),
                       )
