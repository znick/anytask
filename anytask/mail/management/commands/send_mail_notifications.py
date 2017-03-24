# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import get_connection, EmailMultiAlternatives
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext as _

from users.models import UserProfile
import time


class Command(BaseCommand):
    help = "Send new mail notifications via email"

    option_list = BaseCommand.option_list

    def handle(self, **options):
        domain = Site.objects.get_current().domain
        from_email = settings.DEFAULT_FROM_EMAIL
        notify_messages = []
        for user_profile in UserProfile.objects.exclude(send_notify_messages__isnull=True):
            user = user_profile.user
            unread_count = user_profile.send_notify_messages.count()

            lang = user_profile.language
            translation.activate(lang)

            user_profile.send_notify_messages.clear()

            subject = u'{0}, ' + _(u'est_novye_soobshenija').format(user.first_name)

            mail_url = 'http://' + domain + reverse('mail.views.mail_page')
            unread_count_string = get_string(unread_count)

            plain_text = _(u'zdravstvujte') + u', {0}.\n\n' + \
                         _(u'u_vas') + u' {1} {2}.' + '\n' + \
                         _(u'posmotret_soobshenija') + ':\n' + \
                         u'{3}\n\n' + \
                         u'-- \n' + \
                         _(u's_uvazheniem') + ',\n' + \
                         _(u'komanda_anytask') + '.'
            plain_text = plain_text.format(user.first_name, unread_count, unread_count_string, mail_url)

            context = {
                "user": user,
                "user_profile": user_profile,
                "domain": 'http://' + domain,
                "unread_count": unread_count,
                "unread_count_string": unread_count_string
            }
            html = render_to_string('email_notification_mail.html', context)
            notify_messages.append((subject, plain_text, html, from_email, [user.email]))

            translation.deactivate()

        if notify_messages:
            send_mass_mail_html(notify_messages)
            time.sleep(1)


def get_string(num):
    if 11 <= num <= 14:
        return _(u"novyh_soobshenij")
    elif str(num)[-1] == "1":
        return _(u"novoe_soobshenie")
    elif str(num)[-1] in ["2", "3", "4"]:
        return _(u"novyh_soobshenija")
    else:
        return _(u"novyh_soobshenij")


def send_mass_mail_html(datatuple, fail_silently=False, user=None, password=None, connection=None):
    connection = connection or \
                 get_connection(username=user, password=password, fail_silently=fail_silently)
    messages = []
    for subject, plain_text, html, from_email, recipient in datatuple:
        message = EmailMultiAlternatives(subject, plain_text, from_email, recipient)
        message.attach_alternative(html, 'text/html')
        messages.append(message)

    return connection.send_messages(messages)
