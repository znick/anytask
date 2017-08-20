from django.conf.urls import patterns, url

urlpatterns = patterns(
    'search.views',
    url(r'^$', 'search_page'),
    url(r'^users$', 'ajax_search_users'),
    url(r'^courses$', 'ajax_search_courses'),
)
