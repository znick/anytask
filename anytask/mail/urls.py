from django.urls import re_path
import mail.views

urlpatterns = (
    re_path(r'^$', mail.views.mail_page, name="mail.views.mail_page"),
    re_path(r'^ajax_get_mailbox$', mail.views.ajax_get_mailbox,
        name="mail.views.ajax_get_mailbox"),
    re_path(r'^ajax_get_message$', mail.views.ajax_get_message,
        name="mail.views.ajax_get_message"),
    re_path(r'^ajax_send_message$', mail.views.ajax_send_message,
        name="mail.views.ajax_send_message"),
)
