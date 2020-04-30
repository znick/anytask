from django.conf.urls import patterns, url
import search.views

urlpatterns = (
    url(r'^$', search.views.search_page),
    url(r'^users$', search.views.ajax_search_users),
    url(r'^courses$', search.views.ajax_search_courses),
)
