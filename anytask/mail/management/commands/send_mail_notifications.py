# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext as _
from django.utils.html import strip_tags

from mail.common import send_mass_mail_html, render_mail

from users.models import UserProfile
from mail.models import Message

import time


class Command(BaseCommand):
    help = "Send new mail notifications via email"

    option_list = BaseCommand.option_list

    def handle(self, **options):
        domain = Site.objects.get_current().domain
        from_email = settings.DEFAULT_FROM_EMAIL

        if hasattr(settings, 'SEND_MESSAGE_FULLTEXT') and settings.SEND_MESSAGE_FULLTEXT:
            notify_messages = send_fulltext(domain, from_email)
        else:
            notify_messages = [send_only_notify(domain, from_email)]

        for messages in notify_messages:
            if messages:
                send_mass_mail_html(messages)
                time.sleep(1)


def send_only_notify(domain, from_email):
    notify_messages = []

    for user_profile in UserProfile.objects.exclude(send_notify_messages__isnull=True).select_related('user'):
        user = user_profile.user
        unread_count = user_profile.send_notify_messages.count()

        lang = user_profile.language
        translation.activate(lang)

        user_profile.send_notify_messages.clear()

        subject = u'{0}, '.format(user.first_name) + _(u'est_novye_soobshenija')

        unread_count_string = get_string(unread_count)

        context = {
            "user": user,
            "user_profile": user_profile,
            "domain": 'http://' + domain,
            "unread_count": unread_count,
            "unread_count_string": unread_count_string
        }

        plain_text = render_to_string('email_notification_mail.txt', context)
        html = render_to_string('email_notification_mail.html', context)
        notify_messages.append((subject, plain_text, html, from_email, [user.email]))

        translation.deactivate()

    return notify_messages


def send_fulltext(domain, from_email):
    notify_messages = []

    for i_message, message in enumerate(Message.objects.exclude(send_notify_messages__isnull=True)
                                                .prefetch_related('recipients')):
        notify_messages.append([])
        for user in message.recipients.all():
            user_profile = user.get_profile()
            user_profile.send_notify_messages.remove(message)

            lang = user_profile.language
            translation.activate(lang)

            subject = message.title
            message_text = render_mail(message, user)

            plain_text = strip_tags(message_text).replace('&nbsp;', ' ')

            context = {
                "message_text": message_text,
            }
            html = render_to_string('email_fulltext_mail.html', context)

            notify_messages[i_message].append((subject, plain_text, html, from_email, [user.email]))

            translation.deactivate()

    return notify_messages


def get_string(num):
    if 11 <= num <= 14:
        return _(u"novyh_soobshenij")
    elif str(num)[-1] == "1":
        return _(u"novoe_soobshenie")
    elif str(num)[-1] in ["2", "3", "4"]:
        return _(u"novyh_soobshenija")
    else:
        return _(u"novyh_soobshenij")
