# -*- coding: utf-8 -*-

from django.core.mail import get_connection, EmailMultiAlternatives

import logging

logger = logging.getLogger('django.request')


def send_mass_mail_html(datatuple, fail_silently=False, user=None, password=None, connection=None):
    connection = connection or \
                 get_connection(username=user, password=password, fail_silently=fail_silently)
    messages = []
    for subject, plain_text, html, from_email, recipient in datatuple:
        message = EmailMultiAlternatives(subject, plain_text, from_email, recipient)
        message.attach_alternative(html, 'text/html')
        messages.append(message)

    return connection.send_messages(messages)
