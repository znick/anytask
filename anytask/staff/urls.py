from django.conf.urls import patterns, url

urlpatterns = patterns('staff.views',
    url(r'^$', 'staff_page'),
    url(r'^/filter', 'user_filter_by_status_page'),
    url(r'^/ajax_change_status$', 'ajax_change_status'),
    url(r'^/ajax_save_ids', 'ajax_save_ids'),
    url(r'/gradebook$', 'get_gradebook'),
    url(r'/gradebook/(?P<statuses>\w+)$', 'gradebook_page'),
    url(r'^/roles$', 'roles_page'),
    url(r'^/ajax_change_roles$', 'ajax_change_roles'),
    url(r'^/roles/assign$', 'roles_assign_page'),
    url(r'^/ajax_get_user_roles_info$', 'ajax_get_user_roles_info'),
    url(r'^/ajax_save_user_roles$', 'ajax_save_user_roles'),
)
