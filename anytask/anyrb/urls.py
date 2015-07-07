from django.conf.urls import patterns, url

urlpatterns = patterns('anyrb.views',
    url(r'^update/(?P<review_id>\d+)$', 'message_from_rb'),

)
