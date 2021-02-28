from django.conf.urls import url
import staff.views

urlpatterns = (
    url(r'^$', staff.views.staff_page, name="staff.views.staff_page"),
    url(r'^ajax_change_status$', staff.views.ajax_change_status,
        name="staff.views.ajax_change_status"),
    url(r'^ajax_save_ids', staff.views.ajax_save_ids,
        name="staff.views.ajax_save_ids"),
    url(r'gradebook/$', staff.views.get_gradebook,
        name="staff.views.get_gradebook"),
    url(r'gradebook/(?P<statuses>\w+)$', staff.views.gradebook_page,
        name="staff.views.gradebook_page"),
    url(r'gradebook_page', staff.views.gradebook_page,
        name="staff.views.gradebook_page")
)
