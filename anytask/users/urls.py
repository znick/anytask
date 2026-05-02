from django.urls import re_path
import users.views

urlpatterns = (
    re_path(r'^my_tasks/$', users.views.my_tasks,
        name="users.views.my_tasks"),
    re_path(r'^add_user_to_group/$', users.views.add_user_to_group,
        name="users.views.add_user_to_group"),
    re_path(r'^ya_oauth_request/(?P<type_of_oauth>\w+)$', users.views.ya_oauth_request,
        name="users.views.ya_oauth_request"),
    re_path(r'^ya_oauth_response/(?P<type_of_oauth>\w+)$', users.views.ya_oauth_response,
        name="users.views.ya_oauth_response"),
    re_path(r'^ya_oauth_disable/(?P<type_of_oauth>\w+)$', users.views.ya_oauth_disable,
        name="users.views.ya_oauth_disable"),
    re_path(r'^ya_oauth_forbidden/(?P<type_of_oauth>\w+)$', users.views.ya_oauth_forbidden,
        name="users.views.ya_oauth_forbidden"),
    re_path(r'^ya_oauth_changed/$', users.views.ya_oauth_changed,
        name="users.views.ya_oauth_changed"),
    re_path(r'^(?P<username>.*)/courses', users.views.user_courses,
        name="users.views.user_courses"),
    re_path(r'^activate_invite$', users.views.activate_invite,
        name="users.views.activate_invite"),
    re_path(r'^settings$', users.views.profile_settings,
        name="users.views.profile_settings"),
    re_path(r'^(?P<username>.*)/profile_history', users.views.profile_history,
        name="users.views.profile_history"),
    re_path(r'^(?P<username>.*)/set_user_statuses', users.views.set_user_statuses,
        name="users.views.set_user_statuses"),
    re_path(r'^ajax_edit_user_info$', users.views.ajax_edit_user_info,
        name="users.views.ajax_edit_user_info")
)
