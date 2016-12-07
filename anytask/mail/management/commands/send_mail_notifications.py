# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import get_connection, EmailMultiAlternatives
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

from users.models import UserProfile
import time


class Command(BaseCommand):
    help = "Send new mail notifications via email"

    option_list = BaseCommand.option_list

    def handle(self, **options):
        notify_messages = []
        for user_profile in UserProfile.objects.exclude(send_notify_messages__isnull=True):
            user = user_profile.user
            unread_count = user_profile.send_notify_messages.count()

            user_profile.send_notify_messages.clear()

            subject = u'{0}, у вас есть новые сообщения'.format(user.first_name)

            domain = Site.objects.get_current().domain
            mail_url = 'http://' + domain + reverse('mail.views.mail_page')
            unread_count_string = get_string(unread_count)

            plain_text = u'Здравствуйте, {0}.\n\n' + \
                         u'У вас {1} {2}.\n' + \
                         u'Посмотреть сообщения:\n' + \
                         u'{3}\n\n' + \
                         u'-- \n' + \
                         u'С уважением,\n' + \
                         u'команда Anytask.'
            plain_text = plain_text.format(user.first_name, unread_count, unread_count_string, mail_url)

            context = {
                "user": user,
                "user_profile": user_profile,
                "domain": 'http://' + domain,
                "unread_count": unread_count,
                "unread_count_string": unread_count_string
            }
            html = render_to_string('email_notification_mail.html', context)

            from_email = settings.DEFAULT_FROM_EMAIL
            notify_messages.append((subject, plain_text, html, from_email, [user.email]))

        if notify_messages:
            send_mass_mail_html(notify_messages)
            time.sleep(1)


def get_string(num):
    if 11 <= num <= 14:
        return u"новых сообщений"
    elif str(num)[-1] == "1":
        return u"новое сообщение"
    elif str(num)[-1] in ["2", "3", "4"]:
        return u"новых сообщения"
    else:
        return u"новых сообщений"


def send_mass_mail_html(datatuple, fail_silently=False, user=None, password=None, connection=None):
    connection = connection or \
                 get_connection(username=user, password=password, fail_silently=fail_silently)
    messages = []
    for subject, plain_text, html, from_email, recipient in datatuple:
        message = EmailMultiAlternatives(subject, plain_text, from_email, recipient)
        message.attach_alternative(html, 'text/html')
        messages.append(message)

    return connection.send_messages(messages)
