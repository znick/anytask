# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.core.mail import send_mass_mail
from django.contrib.sites.models import Site
from django.conf import settings

from issues.models import Issue


class Command(BaseCommand):
    help = "Send notifications via email"

    option_list = BaseCommand.option_list
    def handle(self, **options):
        notify_messages = []
        issues = Issue.objects.all()
        domain = Site.objects.get_current().domain

        for issue in issues:
            events = issue.get_history().exclude(sended_notify=True)
            message_header = 'http://' + domain + \
                              issue.get_absolute_url() + '\n\n'

            message_body = []
            empty_message = True

            for event in events:
                message_body.append(event.get_notify_message())
                message_body.append('-' * 79)
                event.sended_notify = True
                event.save()

            if message_body:
                empty_message = False

            message_body.append('')
            message_body.append(u'С уважением,')
            message_body.append(u'команда Anytask')
            message_text = message_header + '\n'.join(message_body)

            subject = u'{0} {1} {2}'.\
            format(issue, issue.student.last_name, issue.student.first_name)
            from_email = settings.DEFAULT_FROM_EMAIL

            def get_message(email):
                return (subject, message_text, from_email, [email])


            if not empty_message:
                if issue.student.email:
                    notify_messages.append(get_message(issue.student.email))
                if issue.responsible:
                    if issue.responsible.email:
                        notify_messages.append(get_message(issue.responsible.email))
                for follower in issue.followers.all():
                    if follower.email:
                        notify_messages.append(get_message(follower.email))
        send_mass_mail(notify_messages)

