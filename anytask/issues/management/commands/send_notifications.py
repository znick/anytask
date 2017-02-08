# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.core.mail import get_connection, EmailMultiAlternatives
from django.contrib.sites.models import Site
from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext as _

from issues.models import Issue
from issues.models import Event
import time


class Command(BaseCommand):
    help = "Send notifications via email"

    option_list = BaseCommand.option_list
    def handle(self, **options):
        all_events = Event.objects.filter(sended_notify=False).exclude(
            Q(author__isnull=True) | Q(field__name='review_id')).order_by("issue")
        issues = Issue.objects.filter(event__in=all_events).all()
        domain = Site.objects.get_current().domain

        for issue in issues:
            events = all_events.filter(issue=issue).all()
            issue_url = 'http://' + domain + issue.get_absolute_url()
            message_header = '<div>' + \
                             '<p>' + _(u'Здравствуйте, {0}.') + '<br></p>' + \
                             '<p>' + _(u'В задаче {1}, в который вы являетесь ') + '<strong>{2}</strong>, ' + \
                             _(u'появились новые комментарии: ') + '<br></p>' + \
                             '</div>'

            messages_author = []
            messages_body = []
            empty_message = True

            events_to_send = []
            for event in events:
                messages_author.append(event.author_id)
                messages_body.append('<div style="margin:20px">' +
                                     '<pre>' +
                                     event.get_notify_message().replace('}', '}}').replace('{', '{{') +
                                     '\n' + '-' * 79 +
                                     '</pre>' +
                                     '</div>')
                event.sended_notify = True
                events_to_send.append(event)
                empty_message = False

            message_footer = '<div>' + \
                             u'-- <br>' + \
                             u'{0}<br>'.format(_(u'С уважением,')) + \
                             u'{0}<br>'.format(_(u'команда Anytask.')) + \
                             '</div>'

            subject = _(u'Курс: {0} | Задача: {1} | Студент: {2} {3}').\
                format(issue.task.course, issue.task.title, issue.student.last_name, issue.student.first_name)

            from_email = settings.DEFAULT_FROM_EMAIL

            def get_html_url(url, text):
                return u'<a href="' + url + u'">' + text + u'</a>'

            def get_message(email):
                return (subject, message_text, from_email, [email])

            notify_messages = []
            if not empty_message:
                excluded_ids = []
                if issue.student.email:
                    message_body_text = get_message_body(messages_author, messages_body, issue.student)
                    if message_body_text:
                        message_text = message_header.format(issue.student.first_name,
                                                             get_html_url(issue_url, issue.task.title),
                                                             _(u'студентом')) + \
                                       message_body_text + \
                                       message_footer

                        notify_messages.append(get_message(issue.student.email))
                        excluded_ids.append(issue.student.id)

                if issue.responsible:
                    if issue.responsible.email:
                        message_body_text = get_message_body(messages_author, messages_body, issue.responsible)
                        if message_body_text:
                            message_text = message_header.format(issue.responsible.first_name,
                                                                 get_html_url(issue_url, issue.task.title),
                                                                 _(u'проверяющим')) + \
                                           message_body_text + \
                                           message_footer

                            notify_messages.append(get_message(issue.responsible.email))
                            excluded_ids.append(issue.responsible.id)

                for follower in issue.followers.exclude(id__in=excluded_ids):
                    if follower.email:
                        message_body_text = get_message_body(messages_author, messages_body, follower)
                        if message_body_text:
                            message_text = message_header.format(follower.first_name,
                                                                 get_html_url(issue_url, issue.task.title),
                                                                 _(u'наблюдателем')) + \
                                           message_body_text + \
                                           message_footer

                            notify_messages.append(get_message(follower.email))
                send_mass_mail_html(notify_messages)
                time.sleep(1)

            for event in events_to_send:
                event.save()


def get_message_body(messages_author, messages_body, author):
    s = ''
    if author.get_profile().send_my_own_events:
        s = ''.join(messages_body)
    else:
        for author_id, text in zip(messages_author, messages_body):
            if author_id != author.id:
                s += text
    return s


def send_mass_mail_html(datatuple, fail_silently=False, user=None, password=None, connection=None):
    connection = connection or \
                 get_connection(username=user, password=password, fail_silently=fail_silently)
    messages = []
    for subject, html, from_email, recipient in datatuple:
        message = EmailMultiAlternatives(subject, '...', from_email, recipient)
        message.attach_alternative(html, 'text/html')
        messages.append(message)

    return connection.send_messages(messages)
