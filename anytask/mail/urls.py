from django.conf.urls import url
import mail.views

urlpatterns = (
    url(r'^$', mail.views.mail_page),
    url(r'^ajax_get_mailbox$', mail.views.ajax_get_mailbox),
    url(r'^ajax_get_message$', mail.views.ajax_get_message),
    url(r'^ajax_send_message$', mail.views.ajax_send_message),
)
