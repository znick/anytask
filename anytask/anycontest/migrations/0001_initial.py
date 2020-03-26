# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ContestSubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('run_id', models.CharField(max_length=191, blank=True)),
                ('compiler_id', models.CharField(max_length=191, blank=True)),
                ('send_error', models.TextField(null=True, blank=True)),
                ('got_verdict', models.BooleanField(default=False)),
                ('full_response', models.TextField(null=True, blank=True)),
                ('verdict', models.TextField(null=True, blank=True)),
                ('precompile_checks', models.TextField(null=True, blank=True)),
                ('compile_log', models.TextField(null=True, blank=True)),
                ('used_time', models.IntegerField(null=True, blank=True)),
                ('used_memory', models.IntegerField(null=True, blank=True)),
                ('error', models.TextField(null=True, blank=True)),
                ('message', models.TextField(null=True, blank=True)),
                ('test_number', models.IntegerField(null=True, blank=True)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('sended_notify', models.BooleanField(default=False)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
