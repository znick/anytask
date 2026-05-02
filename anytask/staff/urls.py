from django.urls import re_path
import staff.views

urlpatterns = (
    re_path(r'^$', staff.views.staff_page, name="staff.views.staff_page"),
    re_path(r'^ajax_change_status$', staff.views.ajax_change_status,
        name="staff.views.ajax_change_status"),
    re_path(r'^ajax_save_ids', staff.views.ajax_save_ids,
        name="staff.views.ajax_save_ids"),
    re_path(r'gradebook/$', staff.views.get_gradebook,
        name="staff.views.get_gradebook"),
    re_path(r'gradebook/(?P<statuses>\w+)$', staff.views.gradebook_page,
        name="staff.views.gradebook_page"),
    re_path(r'gradebook_page', staff.views.gradebook_page,
        name="staff.views.gradebook_page")
)
