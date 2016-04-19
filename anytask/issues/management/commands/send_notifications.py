# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.core.mail import get_connection, EmailMultiAlternatives
from django.contrib.sites.models import Site
from django.conf import settings

from issues.models import Issue
import time


class Command(BaseCommand):
    help = "Send notifications via email"

    option_list = BaseCommand.option_list
    def handle(self, **options):
        issues = Issue.objects.all()
        domain = Site.objects.get_current().domain

        for issue in issues:
            events = issue.get_history().exclude(sended_notify=True)
            issue_url = 'http://' + domain + issue.get_absolute_url()
            message_header = '<div>' + \
                             u'<p>Здравствуйте, {0}.<br></p>' + \
                             u'<p>В задаче {1}, в который вы являетесь <strong>{2}</strong>, ' + \
                             u'появились новые комментарии: <br></p>' + \
                             '</div>'

            message_body = []
            empty_message = True

            events_to_send = []
            for event in events:
                message_body.append('<div style="margin:20px">')
                message_body.append('<pre>')
                message_body.append(event.get_notify_message().replace('}','}}').replace('{','{{'))
                message_body.append('-' * 79)
                message_body.append('</pre>')
                message_body.append('</div>')
                event.sended_notify = True
                events_to_send.append(event)

            if message_body:
                empty_message = False

            message_body.append('<div>')
            message_body.append(u'-- <br>')
            message_body.append(u'С уважением,<br>')
            message_body.append(u'команда Anytask.<br>')
            message_body.append('</div>')
            message = message_header + '\n'.join(message_body)

            subject = u'Курс: {0} | Задача: {1} | Студент: {2} {3}'.\
                format(issue.task.course, issue.task.title, issue.student.last_name, issue.student.first_name)

            from_email = settings.DEFAULT_FROM_EMAIL

            def get_html_url(url, text):
                return u'<a href="' + url + u'">' + text + u'</a>'

            def get_message(email):
                return (subject, message_text, from_email, [email])

            notify_messages = []
            if not empty_message:
                if issue.student.email:
                    message_text = message.\
                        format(issue.student.first_name, get_html_url(issue_url, issue.task.title), u'студентом')
                    notify_messages.append(get_message(issue.student.email))
                if issue.responsible:
                    if issue.responsible.email:
                        message_text = message.\
                            format(issue.responsible.first_name, get_html_url(issue_url, issue.task.title), u'проверяющим')
                        notify_messages.append(get_message(issue.responsible.email))
                for follower in issue.followers.all():
                    if follower.email:
                        message_text = message.\
                            format(follower.first_name, get_html_url(issue_url, issue.task.title), u'наблюдателем')
                        notify_messages.append(get_message(follower.email))
                send_mass_mail_html(notify_messages)
                time.sleep(1)

            for event in events_to_send:
                event.save()


def send_mass_mail_html(datatuple, fail_silently=False, user=None, password=None, connection=None):
    connection = connection or \
                 get_connection(username=user, password=password, fail_silently=fail_silently)
    messages = []
    for subject, html, from_email, recipient in datatuple:
        message = EmailMultiAlternatives(subject, '...', from_email, recipient)
        message.attach_alternative(html, 'text/html')
        messages.append(message)

    return connection.send_messages(messages)
