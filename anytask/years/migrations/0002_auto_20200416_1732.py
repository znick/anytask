# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('years', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='year',
            name='added_time',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='year',
            name='update_time',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
