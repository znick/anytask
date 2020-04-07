# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Year',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_year', models.IntegerField(unique=True, db_index=True)),
                ('added_time', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True)),
                ('update_time', models.DateTimeField(default=django.utils.timezone.now, auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
