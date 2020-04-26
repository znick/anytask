# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_auto_20200328_1939'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='added_time',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='course',
            name='update_time',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='studentcoursemark',
            name='update_time',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
