import search.views
from django.urls import re_path

urlpatterns = (
    re_path(r'^$', search.views.search_page, name="search.views.search_page"),
    re_path(r'^users$', search.views.ajax_search_users,
        name="search.views.ajax_search_users"),
    re_path(r'^courses$', search.views.ajax_search_courses,
        name="search.views.ajax_search_courses"),
)
