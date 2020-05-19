import search.views
from django.conf.urls import url

urlpatterns = (
    url(r'^$', search.views.search_page, name="search.views.search_page"),
    url(r'^users$', search.views.ajax_search_users,
        name="search.views.ajax_search_users"),
    url(r'^courses$', search.views.ajax_search_courses,
        name="search.views.ajax_search_courses"),
)
