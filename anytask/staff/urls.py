from django.conf.urls import patterns, url

urlpatterns = patterns(
    'staff.views',
    url(r'^$', 'staff_page'),
    url(r'^ajax_change_status$', 'ajax_change_status'),
    url(r'^ajax_save_ids', 'ajax_save_ids'),
    url(r'/gradebook/$', 'get_gradebook'),
    url(r'/gradebook/(?P<statuses>\w+)$', 'gradebook_page'),
    url(r'/gradebook_page', 'gradebook_page')
)
