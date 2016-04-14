# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.core.mail import send_mass_mail
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
            message_header = u'Здравствуйте, {0}.\n\n' + \
                             u'В задаче "{1}", в который вы являетесь {2}, появились новые комментарии: \n' + \
                             'http://' + domain + \
                             issue.get_absolute_url() + '\n\n'

            message_body = []
            empty_message = True

            events_to_send = []
            for event in events:
                message_body.append(event.get_notify_message())
                message_body.append('-' * 79)
                event.sended_notify = True
                events_to_send.append(event)

            if message_body:
                empty_message = False

            message_body.append('')
            message_body.append(u'С уважением,')
            message_body.append(u'команда Anytask')
            message_text = message_header + '\n'.join(message_body)
            print (message_text);
            subject = u'Курс: {0} | Задача: {1} | Студент: {2} {3}'.\
                format(issue.task.course, issue.task.title, issue.student.last_name, issue.student.first_name)
            print (subject)
            from_email = settings.DEFAULT_FROM_EMAIL

            def get_message(email):
                return (subject, message_text, from_email, [email])

            notify_messages = []
            if not empty_message:
                if issue.student.email:
                    message_text = message_text.\
                        format(issue.student.first_name, issue.task.title, u'студентом')
                    notify_messages.append(get_message(issue.student.email))
                if issue.responsible:
                    if issue.responsible.email:
                        message_text = message_text.\
                            format(issue.responsible.first_name, issue.task.title, u'проверяющим')
                        notify_messages.append(get_message(issue.responsible.email))
                for follower in issue.followers.all():
                    if follower.email:
                        message_text = message_text.\
                            format(follower.first_name, issue.task.title, u'наблюдателем')
                        notify_messages.append(get_message(follower.email))
                send_mass_mail(notify_messages)
                time.sleep(1)

            for event in events_to_send:
                event.save()
