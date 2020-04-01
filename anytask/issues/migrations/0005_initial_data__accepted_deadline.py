# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forward(apps, schema_editor):
    apps.get_model('issues', 'IssueStatus')(
        **{'name': u'{"ru": "Зачтено после дедлайна", "en": "Accepted after deadline"}',
                   'tag': 'accepted_after_deadline',
                   'color': '#ACCD8C',
                   'hidden': False}).save()


class Migration(migrations.Migration):

    dependencies = [
        ('issues', '0004_initial_data_issuestatusfield'),
    ]

    operations = [
        migrations.RunPython(forward)
    ]
