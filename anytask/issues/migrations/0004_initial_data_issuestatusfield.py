# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forward(apps, schema_editor):
    IssueStatus = apps.get_model('issues', 'IssueStatus')
    IssueStatusSystem = apps.get_model('issues', 'IssueStatusSystem')

    IssueStatus(**{'name': u'{"ru": "Новый", "en": "New"}',
                       'tag': 'new',
                       'color': '#818A91',
                       'hidden': True}).save()
    # pk 2
    IssueStatus(**{'name': u'{"ru": "На автоматической проверке", "en": "Auto-checking"}',
                       'tag': 'auto_verification',
                       'color': '#818A91',
                       'hidden': True}).save()
    # pk 3
    IssueStatus(**{'name': u'{"ru": "На проверке", "en": "Checking"}',
                       'tag': 'verification',
                       'color': '#F0AD4E',
                       'hidden': False}).save()
    # pk 4
    IssueStatus(**{'name': u'{"ru": "На доработке", "en": "Revising"}',
                       'tag': 'rework',
                       'color': '#D9534F',
                       'hidden': False}).save()
    # pk 5
    IssueStatus(**{'name': u'{"ru": "Зачтено", "en": "Accepted"}',
                       'tag': 'accepted',
                       'color': '#5CB85C',
                       'hidden': False}).save()
    # pk 6
    IssueStatus(**{'name': u'{"ru": "Требуется информация", "en": "Need information"}',
                       'tag': 'need_info',
                       'color': '#5BC0DE',
                       'hidden': True}).save()

    # default IssueStatusSystem
    IssueStatusSystem(**{'name': u'Стандартная система'}).save()
    issue_status_system = IssueStatusSystem.objects.get(pk=1)
    issue_status_system.statuses = [IssueStatus.objects.get(pk=3),
                                    IssueStatus.objects.get(pk=4),
                                    IssueStatus.objects.get(pk=5)]
    issue_status_system.save()


class Migration(migrations.Migration):

    dependencies = [
        ('issues', '0003_initial_data'),
    ]

    operations = [
        migrations.RunPython(forward)
    ]
