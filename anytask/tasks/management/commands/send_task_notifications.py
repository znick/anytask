# -*- coding: utf-8 -*-

import tasks.admin

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

from django.utils.translation import ugettext as _

from tasks.models import Task
from mail.management.commands.send_mail_notifications import send_mass_mail_html

import time
import reversion


class Command(BaseCommand):
    help = "Send notifications about task changes via email"

    option_list = BaseCommand.option_list

    def handle(self, **options):
        DIFF_FIELDS = [u'title', u'task_text', u'score_max', u'deadline_time']
        DIFF_FIELDS_STR = [
            _(u'nazvanie').lower(),
            _(u'formulirovka').lower(),
            _(u'max_ball').lower(),
            _(u'data_sdachi').lower()
        ]
        students_tasks_info = {}
        for task in Task.objects.filter(sended_notify=False):
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
                    if version.field_dict[field] != version_list[i_version_next].field_dict[field]:
                        task_info[i_field] = DIFF_FIELDS_STR[i_field]
                        task_changed = True
                if not version.field_dict['is_hidden'] and version_list[i_version_next].field_dict['is_hidden']:
                    task_created = True

            if task_created or task_changed:
                task_info = (task, task_created) + tuple(filter(lambda a: a != '', task_info))

                for group in task.groups.all():
                    for student in group.students.all():
                        if student.id in students_tasks_info:
                            if course.id in students_tasks_info[student.id]:
                                students_tasks_info[student.id][course.id][task.id] = task_info
                            else:
                                students_tasks_info[student.id][course.id] = {
                                    'course': course,
                                    task.id: task_info
                                }
                        else:
                            students_tasks_info[student.id] = {
                                'user': student,
                                course.id: {
                                    'course': course,
                                    task.id: task_info
                                }
                            }

            with reversion.create_revision():
                task.sended_notify = True
                task.save()
                reversion.set_comment("Send notification")

        domain = Site.objects.get_current().domain
        from_email = settings.DEFAULT_FROM_EMAIL
        plain_header = _(u'zdravstvujte') + u', {0}.\n\n'
        plain_body_course = _(u'v_kurse_izmenilis_zadachi') + u'\n'\
                            u'{1}\n' + \
                            _(u'pereyti_v_kurs') + u'\n' \
                            u'{2}\n\n'
        plain_body_task = _(u'v_zadache') + u' "{0}" ' + _(u'izmenilis') + u' {1}\n'
        plain_body_task_new = u'  - ' + _(u'dobavlena_zadacha') + u' "{0}"\n'

        plain_footer = u'\n\n' + \
                       u'-- \n' + \
                       _(u's_uvazheniem') + u',\n' + \
                       _(u'komanda_anytask')
        notify_messages = []
        for key_user, courses_info in students_tasks_info.iteritems():
            user = courses_info['user']
            subject = _(u'proizoshli_izmeneniya_v_kursah').format(user.first_name)

            plain_body = u''
            for key_course, tasks_info in courses_info.iteritems():
                if key_course == 'user':
                    continue

                task_text = u''
                for key_task, task_info in tasks_info.iteritems():
                    if key_task == 'course':
                        continue
                    if task_info[1]:
                        task_text += plain_body_task_new.format(task_info[0].title)
                    else:
                        task_text += plain_body_task.format(task_info[0].title, u', '.join(task_info[2:]))

                course_url = 'http://' + domain + tasks_info['course'].get_absolute_url()
                plain_body += plain_body_course.format(tasks_info['course'].name, task_text, course_url)

            plain_text = plain_header.format(user.first_name) + plain_body + plain_footer
            context = {
                "user": user,
                "domain": 'http://' + domain,
                "courses_info": courses_info,
            }
            html = render_to_string('email_notification_task.html', context)
            notify_messages.append((subject, plain_text, html, from_email, [user.email]))

        if notify_messages:
            send_mass_mail_html(notify_messages)
            time.sleep(1)
