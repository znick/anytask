# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings
from django.db.models import Q
from django.utils import translation, timezone
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_noop as _noop
from django.template.loader import render_to_string

from mail.common import send_mass_mail_html

from issues.models import Issue, Event
import time


class Command(BaseCommand):
    help = "Send notifications via email"

    option_list = BaseCommand.option_list

    def handle(self, **options):
        start_time = time.time()
        num_sent = 0
        sleep_time = 0
        all_events = Event.objects \
            .filter(sended_notify=False) \
            .exclude(Q(author__isnull=True) | Q(author__username="anytask") | Q(field__name='review_id')) \
            .distinct() \
            .select_related("issue", "author") \
            .prefetch_related("file_set") \
            .order_by("issue")
        domain = Site.objects.get_current().domain
        from_email = settings.DEFAULT_FROM_EMAIL
        for issue in Issue.objects\
                .filter(event__in=all_events) \
                .distinct() \
                .select_related("student", "responsible", "task", "task__course") \
                .prefetch_related("followers"):
            events = all_events.filter(issue=issue)
            if not events:
                continue
            notify_messages = []
            excluded_ids = []
            if issue.student.email:
                message = get_message(issue.student, _noop(u'studentom'), issue, events, from_email, domain)
                if message:
                    notify_messages.append(message)
                excluded_ids.append(issue.student.id)

            if issue.responsible and issue.responsible.id not in excluded_ids:
                excluded_ids.append(issue.student.id)
                if issue.responsible.email:
                    message = get_message(
                        issue.responsible, _noop(u'proverjaushim'), issue, events, from_email, domain
                    )
                    if message:
                        notify_messages.append(message)

            for follower in issue.followers.exclude(id__in=excluded_ids):
                if follower.email:
                    message = get_message(follower, _noop(u'nabludatelem'), issue, events, from_email, domain)
                    if message:
                        notify_messages.append(message)

            if notify_messages:
                num_sent += send_mass_mail_html(notify_messages)
                time.sleep(1)
                sleep_time += 1

            for event in events:
                event.sended_notify = True
                event.save()

        # logging to cron log
        print("Command send_issue_notifications send {0} email(s) and took {1} seconds (sleep {2} seconds)"
              .format(num_sent, time.time() - start_time, sleep_time))


def get_message(user, user_type, issue, events, from_email, domain):
    user_profile = user.profile

    if not user_profile.send_my_own_events:
        events = events.exclude(author_id=user.id)

    if not events:
        return ()

    lang = user_profile.language
    translation.activate(lang)
    timezone.activate(user_profile.time_zone)

    subject = (_(u'kurs') + u': {0} | ' + _(u'zadacha') + u': {1} | ' + _(u'student') + u': {2} {3}'). \
        format(issue.task.course.name, issue.task.get_title(lang), issue.student.last_name, issue.student.first_name)

    context = {
        "user": user,
        "domain": domain,
        "title": subject,
        "user_type": user_type,
        "issue": issue,
        "events": events,
        "STATIC_URL": settings.STATIC_URL,
    }

    plain_text = render_to_string('email_issue_notification.txt', context)
    html = render_to_string('email_issue_notification.html', context)
    translation.deactivate()
    timezone.deactivate()

    return subject, plain_text, html, from_email, [user.email]
