from django.urls import re_path
import api.views

urlpatterns = [
    re_path(r'^v1/course/(?P<course_id>\d+)/statuses$', api.views.get_issue_statuses,
        name="api.views.get_issue_statuses"),
    re_path(r'^v1/course/(?P<course_id>\d+)/issues$', api.views.get_issues,
        name="api.views.get_issues"),
    re_path(r'^v1/issue/(?P<issue_id>\d+)/add_comment$', api.views.add_comment,
        name="api.views.add_comment"),
    re_path(r'^v1/issue/(?P<issue_id>\d+)$', api.views.get_or_post_issue,
        name="api.views.get_or_post_issue"),
    re_path(r'^v1/check_user$', api.views.check_user,
        name="api.views.check_user"),
]
