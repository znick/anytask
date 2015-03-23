from django.conf.urls import patterns, url

urlpatterns = patterns('users.views',
    url(r'^add_user_to_group/$', 'add_user_to_group'),
)