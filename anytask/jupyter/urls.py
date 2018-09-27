from django.conf.urls import patterns, url

urlpatterns = patterns('jupyter.views',
                       url(r'^assignments$', 'update_jupyter_task'))
