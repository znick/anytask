# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import colorfield.fields
import common.locale_funcs
import issues.models
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.TextField(max_length=2500, blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('sended_notify', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(max_length=500, null=True, upload_to=issues.models.get_file_path, blank=True)),
                ('deleted', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Issue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('mark', models.FloatField(default=0)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True)),
                ('update_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.CharField(default=b'new', max_length=20, choices=[(b'new', 'novyj'), (b'rework', 'na_dorabotke'), (b'verification', 'na_proverke'), (b'accepted', 'zachteno'), (b'auto_verification', 'na_avtomaticheskoj_proverke'), (b'need_info', 'trebuetsja_informacija')])),
                ('followers', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, blank=True)),
                ('responsible', models.ForeignKey(related_name=b'responsible', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IssueField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=191)),
                ('title', models.CharField(max_length=191, blank=True)),
                ('history_message', models.CharField(max_length=191, blank=True)),
                ('plugin', models.CharField(default=b'FieldDefaultPlugin', max_length=191)),
                ('plugin_version', models.CharField(default=b'0.1', max_length=50)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IssueStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='Format is {"ru": "C\u0435\u043c\u0438\u043d\u0430\u0440", "en": "Seminar", etc.} or {"ru": "C\u0435\u043c\u0438\u043d\u0430\u0440"}', max_length=191, db_index=True, validators=[common.locale_funcs.validate_json])),
                ('tag', models.CharField(blank=True, max_length=191, null=True, choices=[(b'rework', 'rework'), (b'verification', 'verification'), (b'accepted', 'accepted'), (b'seminar', 'seminar'), (b'accepted_after_deadline', 'accepted_after_deadline')])),
                ('color', colorfield.fields.ColorField(default=b'#818A91', max_length=18)),
                ('hidden', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'issue status',
                'verbose_name_plural': 'issue statuses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IssueStatusSystem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=191)),
                ('statuses', models.ManyToManyField(to='issues.IssueStatus', null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='issue',
            name='status_field',
            field=models.ForeignKey(default=1, to='issues.IssueStatus'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issue',
            name='student',
            field=models.ForeignKey(related_name=b'student', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
