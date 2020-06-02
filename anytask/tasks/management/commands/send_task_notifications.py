# -*- coding: utf-8 -*-

import tasks.admin  # NOQA

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext as _

from tasks.models import Task
from mail.common import send_mass_mail_html

import time
from reversion import revisions as reversion
import pytz


def add_timezone(date):
    if date:
        try:
            return date.astimezone(pytz.UTC)
        except ValueError:  # naive
            return date.replace(tzinfo=pytz.UTC)
    return date


class Command(BaseCommand):
    help = "Send notifications about task changes via email"

    option_list = BaseCommand.option_list

    def handle(self, **options):
        start_time = time.time()

        DIFF_FIELDS = [u'title', u'task_text', u'score_max', u'deadline_time']

        students_tasks_info = {}
        for task in Task.objects.filter(sended_notify=False).prefetch_related("groups"):
            course = task.course
            if task.is_hidden:
                continue

            task_created = False
            task_changed = False

            version_list = reversion.get_unique_for_object(task)

            task_info = [''] * len(DIFF_FIELDS)
            for i_version, version in enumerate(version_list):
                if version.field_dict['sended_notify']:
                    break

                i_version_next = i_version + 1
                if i_version_next == len(version_list):
                    task_created = True
                    break
                if not version.field_dict['send_to_users']:
                    continue

                for i_field, field in enumerate(DIFF_FIELDS):
                    if field == u'deadline_time':
                        prev = add_timezone(version.field_dict[field])
                        cur = add_timezone(version_list[i_version_next].field_dict[field])
                    else:
                        prev, cur = version.field_dict[field], version_list[i_version_next].field_dict[field]
                    if prev != cur:
                        task_info[i_field] = field
                        task_changed = True
                if not version.field_dict['is_hidden'] and version_list[i_version_next].field_dict['is_hidden']:
                    task_created = True

            if task_created or task_changed:
                for group in task.groups.all():
                    for student in group.students.all():
                        translation.activate(student.profile.language)
                        diff_fields_str = {
                            u'title': _(u'nazvanie').lower(),
                            u'task_text': _(u'formulirovka').lower(),
                            u'score_max': _(u'max_ball').lower(),
                            u'deadline_time': _(u'data_sdachi').lower()
                        }
                        task_info_changed = (task, task_created) + tuple(map(
                            lambda a: diff_fields_str[a],
                            filter(lambda a: a != '', task_info)
                        ))

                        if student.id in students_tasks_info:
                            if course.id in students_tasks_info[student.id]:
                                students_tasks_info[student.id][course.id][task.id] = task_info_changed
                            else:
                                students_tasks_info[student.id][course.id] = {
                                    'course': course,
                                    task.id: task_info_changed
                                }
                        else:
                            students_tasks_info[student.id] = {
                                'user': student,
                                course.id: {
                                    'course': course,
                                    task.id: task_info_changed
                                }
                            }

                        translation.deactivate()

            with reversion.create_revision():
                task.sended_notify = True
                task.save()
                reversion.set_comment("Send notification")

        domain = Site.objects.get_current().domain
        from_email = settings.DEFAULT_FROM_EMAIL
        notify_messages = []
        for key_user, courses_info in students_tasks_info.items():
            user = courses_info['user']
            if not user.email:
                continue

            lang = user.profile.language
            translation.activate(lang)

            subject = u"{0}, ".format(user.first_name) + _(u'proizoshli_izmeneniya_v_kursah')

            context = {
                "user": user,
                "domain": domain,
                "title": subject,
                "courses_info": courses_info,
            }
            plain_text = render_to_string('email_notification_task.txt', context)
            html = render_to_string('email_notification_task.html', context)
            notify_messages.append((subject, plain_text, html, from_email, [user.email]))
            translation.deactivate()

        num_sent = 0
        if notify_messages:
            num_sent = send_mass_mail_html(notify_messages)

        # logging to cron log
        print("Command send_task_notifications send {0} email(s) and took {1} seconds"
              .format(num_sent, time.time() - start_time))
