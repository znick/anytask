# -*- coding: utf-8 -*-
from django.core.mail import get_connection, EmailMultiAlternatives
from django.conf import settings
from django.template import Template, Context
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext as _
from django.utils.html import strip_tags

import logging
from contextlib import contextmanager

from mail.base import BaseRenderer, BaseSender

logger = logging.getLogger('django.request')


@contextmanager
def enable_translation(user_profile):
    lang = user_profile.language
    translation.activate(lang)
    try:
        yield
    finally:
        translation.deactivate()


class EmailRenderer(BaseRenderer):
    def __init__(self, domain, from_email):
        BaseRenderer.__init__(self)
        self.domain = domain
        self.from_email = from_email

    def render_notification(self, user_profile, unread_messages):
        with enable_translation(user_profile):
            user = user_profile.user

            subject = u'{0}, '.format(user.first_name) + _(u'est_novye_soobshenija')

            unread_count = len(unread_messages)
            unread_count_string = self._get_string(unread_count)

            context = {
                "domain": self.domain,
                "title": subject,
                "user": user,
                "unread_count": unread_count,
                "unread_count_string": unread_count_string,
                "messages": unread_messages,
                "STATIC_URL": settings.STATIC_URL,
            }

            plain_text = render_to_string('email_notification_mail.txt', context)
            html = render_to_string('email_notification_mail.html', context)
            rendered_message = (subject, plain_text, html, self.from_email, [user.email])

        return rendered_message

    def render_fulltext(self, message, recipients):
        rendered_messages = []
        for user in recipients:
            if not user.email:
                continue
            rendered_messages.append(self.__render_fulltext_single(message, user))

        return rendered_messages

    def __render_fulltext_single(self, message, user):
        user_profile = user.profile
        with enable_translation(user_profile):
            subject = message.title
            message_text = self.fill_name(message, user)

            plain_text = strip_tags(message_text).replace('&nbsp;', ' ')

            context = {
                "domain": self.domain,
                "title": subject,
                "message_text": message_text,
            }
            html = render_to_string('email_fulltext_mail.html', context)

            rendered_message = subject, plain_text, html, self.from_email, [user.email]

        return rendered_message

    @classmethod
    def fill_name(cls, message, user):
        if message.variable:
            t = Template(message.text.replace('%', '&#37;'))
            c = Context({
                "last_name": user.last_name,
                "first_name": user.first_name,
            })
            return t.render(c)
        return message.text


class EmailSender(BaseSender):
    def __init__(self, from_email, fail_silently=False, user=None, password=None, connection=None):
        BaseSender.__init__(self)
        self.from_email = from_email
        self.fail_silently = fail_silently
        self.user = user
        self.password = password
        self.connection = connection

    def mass_send(self, prepared_messages):
        # TODO drop from_email from prepared_messages
        connection = self.__get_connection()
        messages = []
        for subject, plain_text, html, from_email, recipient in prepared_messages:
            message = EmailMultiAlternatives(subject, plain_text, from_email, recipient)
            message.attach_alternative(html, 'text/html')
            messages.append(message)

        return connection.send_messages(messages)

    def __get_connection(self):
        return self.connection or get_connection(username=self.user, password=self.password,
                                                 fail_silently=self.fail_silently)
