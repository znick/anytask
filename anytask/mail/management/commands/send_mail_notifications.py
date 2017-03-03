# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from mail.common import send_mass_mail_html

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

            subject = _(u'{0}, у вас есть новые сообщения').format(user.first_name)

            domain = Site.objects.get_current().domain
            mail_url = 'http://' + domain + reverse('mail.views.mail_page')
            unread_count_string = get_string(unread_count)

            plain_text = _(u'Здравствуйте, {0}.') + '\n\n' + \
                         _(u'У вас {1} {2}.') + '\n' + \
                         _(u'Посмотреть сообщения:') + '\n' + \
                         u'{3}\n\n' + \
                         u'-- \n' + \
                         _(u'С уважением,') + '\n' + \
                         _(u'команда Anytask.')
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
        return _(u"новых сообщений")
    elif str(num)[-1] == "1":
        return _(u"новое сообщение")
    elif str(num)[-1] in ["2", "3", "4"]:
        return _(u"новых сообщения")
    else:
        return _(u"новых сообщений")
