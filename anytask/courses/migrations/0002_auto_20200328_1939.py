# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('issues', '0001_initial'),
        ('years', '0001_initial'),
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='issue_fields',
            field=models.ManyToManyField(to='issues.IssueField', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='course',
            name='issue_status_system',
            field=models.ForeignKey(default=1, to='issues.IssueStatusSystem', db_index=False, on_delete=models.DO_NOTHING),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='course',
            name='mark_system',
            field=models.ForeignKey(to='courses.CourseMarkSystem', blank=True, null=True, db_index=False, on_delete=models.DO_NOTHING),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='course',
            name='teachers',
            field=models.ManyToManyField(related_name='course_teachers_set', null=True, to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='course',
            name='year',
            field=models.ForeignKey(default=2020, to='years.Year', on_delete=models.DO_NOTHING),
            preserve_default=True,
        ),
    ]
