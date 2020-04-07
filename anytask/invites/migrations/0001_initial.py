# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(unique=True, max_length=10, db_index=True)),
                ('added_time', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True)),
                ('update_time', models.DateTimeField(default=django.utils.timezone.now, auto_now=True)),
                ('generated_by', models.ForeignKey(related_name=b'invite_generated_by', to=settings.AUTH_USER_MODEL, db_index=False)),
                ('group', models.ForeignKey(to='groups.Group', blank=True, null=True, db_index=False)),
                ('invited_users', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
