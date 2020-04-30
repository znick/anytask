from django.conf.urls import url
import users.views

urlpatterns = (
    url(r'^my_tasks/$', users.views.my_tasks),
    url(r'^add_user_to_group/$', users.views.add_user_to_group),
    url(r'^ya_oauth_request/(?P<type_of_oauth>\w+)$', users.views.ya_oauth_request),
    url(r'^ya_oauth_response/(?P<type_of_oauth>\w+)$', users.views.ya_oauth_response),
    url(r'^ya_oauth_disable/(?P<type_of_oauth>\w+)$', users.views.ya_oauth_disable),
    url(r'^ya_oauth_forbidden/(?P<type_of_oauth>\w+)$', users.views.ya_oauth_forbidden),
    url(r'^ya_oauth_changed/$', users.views.ya_oauth_changed),
    url(r'^(?P<username>.*)/courses', users.views.user_courses),
    url(r'^activate_invite$', users.views.activate_invite),
    url(r'^settings$', users.views.profile_settings),
    url(r'^(?P<username>.*)/profile_history', users.views.profile_history),
    url(r'^(?P<username>.*)/set_user_statuses', users.views.set_user_statuses),
    url(r'^ajax_edit_user_info$', users.views.ajax_edit_user_info)
)
