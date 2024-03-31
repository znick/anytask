# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('issues', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='task',
            field=models.ForeignKey(to='tasks.Task', null=True, on_delete=models.DO_NOTHING),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='issue',
            unique_together=set([('student', 'task')]),
        ),
        migrations.AddField(
            model_name='file',
            name='event',
            field=models.ForeignKey(to='issues.Event', on_delete=models.DO_NOTHING),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='author',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.DO_NOTHING),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='field',
            field=models.ForeignKey(default=1, to='issues.IssueField', on_delete=models.DO_NOTHING),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='issue',
            field=models.ForeignKey(to='issues.Issue', on_delete=models.DO_NOTHING),
            preserve_default=True,
        ),
    ]
