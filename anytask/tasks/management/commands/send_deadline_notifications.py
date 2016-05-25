# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.core.mail import get_connection, EmailMultiAlternatives
from django.contrib.sites.models import Site
from django.conf import settings

from tasks.models import TaskLog
import time


class Command(BaseCommand):
    help = "Send notifications about deadline changes via email"

    option_list = BaseCommand.option_list
    def handle(self, **options):
        tasks = TaskLog.objects.all().exclude(sended_notify=True)
        domain = Site.objects.get_current().domain

        for task in tasks:
            groups = []
            if not task.group:
                groups = task.course.groups.all()
            else:
                groups.append(task.group)
            for group in groups:
                for student in group.students:

                    message_header = '<div>' + \
                                     u'<p>Здравствуйте, {0}.<br></p>' + \
                                     u'<p>В задаче {1}, курса {2}, ' + \
                                     u'новая дата сдачи: <br></p>' + \
                                     '</div>'

                    message_body = []
                    empty_message = True

                    tasks_to_send = []
                    message_body.append('<div style="margin:20px">')
                    message_body.append('<pre>')
                    message_body.append(task.deadline_time)
                    message_body.append('-' * 79)
                    message_body.append('</pre>')
                    message_body.append('</div>')
                    task.sended_notify = True
                    tasks_to_send.append(task)

                    if message_body:
                        empty_message = False

                    message_body.append('<div>')
                    message_body.append(u'-- <br>')
                    message_body.append(u'С уважением,<br>')
                    message_body.append(u'команда Anytask.<br>')
                    message_body.append('</div>')
                    message = message_header + '\n'.join(message_body)

                    subject = u'Курс: {0} | Задача: {1} | Студент: {2} {3}'.\
                        format(task.course, task.title, student.last_name, student.first_name)

                    from_email = settings.DEFAULT_FROM_EMAIL

                    def get_html_url(url, text):
                        return u'<a href="' + url + u'">' + text + u'</a>'

                    def get_message(email):
                        return (subject, message_text, from_email, [email])

                    notify_messages = []
                    if not empty_message:
                        message_text = message.\
                            format(student.first_name, task.title, get_html_url(task.course.get_absolute_url(),task.course))
                        notify_messages.append(get_message(student.email))

                        send_mass_mail_html(notify_messages)
                        time.sleep(1)

                    for task in tasks_to_send:
                        task.save()


def send_mass_mail_html(datatuple, fail_silently=False, user=None, password=None, connection=None):
    connection = connection or \
                 get_connection(username=user, password=password, fail_silently=fail_silently)
    messages = []
    for subject, html, from_email, recipient in datatuple:
        message = EmailMultiAlternatives(subject, '...', from_email, recipient)
        message.attach_alternative(html, 'text/html')
        messages.append(message)

    return connection.send_messages(messages)
