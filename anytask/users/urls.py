from django.conf.urls import patterns, url

urlpatterns = patterns('users.views',
    url(r'^add_user_to_group/$', 'add_user_to_group'),
    url(r'^ya_oauth_request/(?P<type_of_oauth>\w+)$', 'ya_oauth_request'),
    url(r'^ya_oauth_response/(?P<type_of_oauth>\w+)$', 'ya_oauth_response'),
)