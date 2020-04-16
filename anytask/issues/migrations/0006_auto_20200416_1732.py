# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issues', '0005_initial_data__accepted_deadline'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issue',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
