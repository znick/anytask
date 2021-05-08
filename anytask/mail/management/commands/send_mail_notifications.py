# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.sites.models import Site

from mail.common import EmailSender, EmailRenderer
from anytelegram.common import TelegramRenderer, TelegramSender

from users.models import UserProfile
from mail.models import Message

import time


class Command(BaseCommand):
    help = "Send new mail notifications via email"

    def add_arguments(self, parser):
        pass

    def handle(self, **options):
        start_time = time.time()

        domain = Site.objects.get_current().domain
        from_email = settings.DEFAULT_FROM_EMAIL

        email_renderer = EmailRenderer(domain, from_email)
        email_sender = EmailSender(from_email)

        tg_renderer = TelegramRenderer()
        tg_sender = TelegramSender()

        if hasattr(settings, 'SEND_MESSAGE_FULLTEXT') and settings.SEND_MESSAGE_FULLTEXT:
            models_fulltext = extract_fulltext()
            notify_messages_email = list(map(lambda tpl: email_renderer.render_fulltext(*tpl), models_fulltext))
            notify_messages_tg = list(map(lambda tpl: tg_renderer.render_fulltext(*tpl), models_fulltext))
        else:
            models_only_notify = extract_only_notify()
            notify_messages_email = list(map(lambda tpl: email_renderer.render_notification(*tpl), models_only_notify))
            notify_messages_tg = list(map(lambda tpl: tg_renderer.render_notification(*tpl), models_only_notify))

        num_sent_email = 0
        num_sent_tg = 0
        sleep_time = 0
        for messages_email, messages_tg in zip(notify_messages_email, notify_messages_tg):
            sent = False
            if messages_email:
                num_sent_email += email_sender.mass_send([messages_email])
                sent = True
            elif messages_tg:
                num_sent_tg += tg_sender.mass_send([messages_tg])
                sent = True
            if sent:
                time.sleep(1)
                sleep_time += 1

        # logging to cron log
        print "Command send_mail_notifications send {0} email(s), {1} tg message(s) " \
              "and took {2} seconds (sleep {3} seconds)" \
            .format(num_sent_email, num_sent_tg, time.time() - start_time, sleep_time)


def extract_only_notify():
    """
    Returns: list of pairs (user_profile, unread messages)
    """
    notify_messages = []

    for user_profile in UserProfile.objects.exclude(send_notify_messages__isnull=True).select_related('user'):
        user = user_profile.user
        if not user.email:
            continue

        unread_messages = user_profile.send_notify_messages.all()
        unread_count = len(unread_messages)
        if not unread_count:
            continue

        user_profile.send_notify_messages.clear()
        notify_messages.append((user_profile, unread_messages))

    return notify_messages


def extract_fulltext():
    """
    Returns: list of pairs (message, message.recipients)
    """
    notify_messages = []

    for message in Message.objects.exclude(send_notify_messages__isnull=True).prefetch_related('recipients'):
        recipients = message.recipients.all()
        notify_messages.append((message, recipients))

    return notify_messages
