# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('issues', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0001_initial'),
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(db_index=True, max_length=191, null=True, blank=True)),
                ('short_title', models.CharField(db_index=True, max_length=15, null=True, blank=True)),
                ('weight', models.IntegerField(default=0, db_index=True)),
                ('is_hidden', models.BooleanField(default=False, db_index=True)),
                ('task_text', models.TextField(default=None, null=True, blank=True)),
                ('score_max', models.IntegerField(default=0, db_index=True)),
                ('max_students', models.IntegerField(default=0)),
                ('contest_integrated', models.BooleanField(default=False)),
                ('rb_integrated', models.BooleanField(default=False)),
                ('type', models.CharField(default=b'All', max_length=128, choices=[(b'All', 's_obsuzhdeniem'), (b'Only mark', 'tolko_ocenka'), (b'Material', 'material'), (b'Seminar', 'seminar'), (b'Jupyter Notebook', 'jupyter notebook')])),
                ('added_time', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True)),
                ('update_time', models.DateTimeField(default=django.utils.timezone.now, auto_now=True)),
                ('deadline_time', models.DateTimeField(default=None, null=True, blank=True)),
                ('contest_id', models.IntegerField(default=0, db_index=True)),
                ('problem_id', models.CharField(db_index=True, max_length=128, null=True, blank=True)),
                ('send_to_users', models.BooleanField(default=False)),
                ('sended_notify', models.BooleanField(default=True, db_index=True)),
                ('one_file_upload', models.BooleanField(default=False)),
                ('accepted_after_contest_ok', models.BooleanField(default=False)),
                ('score_after_deadline', models.BooleanField(default=True)),
                ('nb_assignment_name', models.CharField(max_length=255, null=True, blank=True)),
                ('course', models.ForeignKey(to='courses.Course')),
                ('group', models.ForeignKey(default=None, blank=True, to='groups.Group', null=True, db_index=False)),
                ('groups', models.ManyToManyField(related_name=b'groups_set', to='groups.Group')),
                ('parent_task', models.ForeignKey(related_name=b'children', blank=True, to='tasks.Task', null=True)),
                ('updated_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True, null=True, db_index=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskGroupRelations',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('position', models.IntegerField(default=0)),
                ('deleted', models.BooleanField(default=False)),
                ('group', models.ForeignKey(to='groups.Group', db_index=False)),
                ('task', models.ForeignKey(to='tasks.Task', db_index=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(db_index=True, max_length=191, null=True, blank=True)),
                ('weight', models.IntegerField(default=0)),
                ('task_text', models.TextField(default=None, null=True, blank=True)),
                ('score_max', models.IntegerField(default=0)),
                ('contest_integrated', models.BooleanField(default=False)),
                ('rb_integrated', models.BooleanField(default=False)),
                ('type', models.CharField(default=b'All', max_length=128, choices=[(b'All', 's_obsuzhdeniem'), (b'Only mark', 'tolko_ocenka')])),
                ('added_time', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True)),
                ('update_time', models.DateTimeField(default=django.utils.timezone.now, auto_now=True)),
                ('deadline_time', models.DateTimeField(default=None, null=True)),
                ('contest_id', models.IntegerField(default=0, db_index=True)),
                ('problem_id', models.CharField(db_index=True, max_length=128, null=True, blank=True)),
                ('course', models.ForeignKey(to='courses.Course', db_index=False)),
                ('group', models.ForeignKey(default=None, blank=True, to='groups.Group', null=True, db_index=False)),
                ('groups', models.ManyToManyField(related_name=b'groups_log_set', to='groups.Group')),
                ('parent_task', models.ForeignKey(related_name=b'parent_task_set', blank=True, to='tasks.TaskLog', null=True)),
                ('updated_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True, null=True, db_index=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaskTaken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.IntegerField(default=0, max_length=1, db_index=True, choices=[(0, 'Task taken'), (1, 'Task cancelled'), (2, 'Task blacklisted'), (3, 'Task scored'), (4, 'TaskTaken deleted')])),
                ('status_check', models.CharField(default=b'EDIT', max_length=5, db_index=True, choices=[(b'EDIT', '\u0414\u043e\u0440\u0435\u0448\u0438\u0432\u0430\u043d\u0438\u0435'), (b'QUEUE', '\u041e\u0436\u0438\u0434\u0430\u0435\u0442 \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0438'), (b'OK', '\u0417\u0430\u0434\u0430\u0447\u0430 \u0437\u0430\u0447\u0442\u0435\u043d\u0430 \u0438/\u0438\u043b\u0438 \u0431\u043e\u043b\u044c\u0448\u0435 \u043d\u0435 \u043f\u0440\u0438\u043d\u0438\u043c\u0430\u0435\u0442\u0441\u044f')])),
                ('taken_time', models.DateTimeField(null=True, blank=True)),
                ('blacklisted_till', models.DateTimeField(null=True, blank=True)),
                ('added_time', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True)),
                ('update_time', models.DateTimeField(default=django.utils.timezone.now, auto_now=True)),
                ('issue', models.ForeignKey(to='issues.Issue', null=True)),
                ('task', models.ForeignKey(to='tasks.Task')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='tasktaken',
            unique_together=set([('user', 'task')]),
        ),
        migrations.AlterUniqueTogether(
            name='taskgrouprelations',
            unique_together=set([('task', 'group')]),
        ),
    ]
