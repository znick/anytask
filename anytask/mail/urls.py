from django.conf.urls import patterns, url

urlpatterns = patterns('mail.views',
                       url(r'^$', 'mail_page'),
                       url(r'^ajax_get_mailbox$', 'ajax_get_mailbox'),
                       url(r'^ajax_get_message$', 'ajax_get_message'),
                       url(r'^ajax_send_message$', 'ajax_send_message'),
)
