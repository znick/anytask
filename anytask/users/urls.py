from django.conf.urls import patterns, url

urlpatterns = patterns('users.views',
    url(r'^my_tasks/$', 'my_tasks'),
    url(r'^add_user_to_group/$', 'add_user_to_group'),
    url(r'^ya_oauth_request/(?P<type_of_oauth>\w+)$', 'ya_oauth_request'),
    url(r'^ya_oauth_response/(?P<type_of_oauth>\w+)$', 'ya_oauth_response'),
    url(r'^ya_oauth_disable/(?P<type_of_oauth>\w+)$', 'ya_oauth_disable'),
    url(r'^ya_oauth_forbidden/$', 'ya_oauth_forbidden'),
    url(r'^ya_oauth_changed/$', 'ya_oauth_changed'),
    url(r'^(?P<username>.*)/courses', 'user_courses'),
    url(r'^activate_invite$', 'activate_invite'),
)
