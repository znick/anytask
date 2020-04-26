# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0002_auto_20200328_1939'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='create_time',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
