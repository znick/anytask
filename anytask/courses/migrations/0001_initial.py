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
            name='Course',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=191, db_index=True)),
                ('name_id', models.CharField(db_index=True, max_length=191, null=True, blank=True)),
                ('information', models.TextField(null=True, blank=True)),
                ('is_active', models.BooleanField(default=False, db_index=True)),
                ('contest_integrated', models.BooleanField(default=False)),
                ('send_rb_and_contest_together', models.BooleanField(default=False)),
                ('rb_integrated', models.BooleanField(default=False)),
                ('take_mark_from_contest', models.BooleanField(default=False)),
                ('send_to_contest_from_users', models.BooleanField(default=False)),
                ('full_transcript', models.BooleanField(default=True)),
                ('private', models.BooleanField(default=True)),
                ('added_time', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True)),
                ('update_time', models.DateTimeField(default=django.utils.timezone.now, auto_now=True)),
                ('can_be_chosen_by_extern', models.BooleanField(default=False)),
                ('show_accepted_after_contest_ok', models.BooleanField(default=False)),
                ('default_accepted_after_contest_ok', models.BooleanField(default=False)),
                ('show_task_one_file_upload', models.BooleanField(default=False)),
                ('default_task_one_file_upload', models.BooleanField(default=False)),
                ('default_task_send_to_users', models.BooleanField(default=False)),
                ('is_python_task', models.BooleanField(default=False)),
                ('max_students_per_task', models.IntegerField(default=0)),
                ('max_incomplete_tasks', models.IntegerField(default=0)),
                ('max_not_scored_tasks', models.IntegerField(default=0)),
                ('has_attendance_log', models.BooleanField(default=False)),
                ('show_contest_run_id', models.BooleanField(default=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CourseMarkSystem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=191)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DefaultTeacher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course', models.ForeignKey(to='courses.Course', on_delete=models.DO_NOTHING)),
                ('group', models.ForeignKey(blank=True, to='groups.Group', null=True, on_delete=models.DO_NOTHING)),
                ('teacher', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True, null=True, db_index=False, on_delete=models.DO_NOTHING)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FilenameExtension',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=10)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MarkField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=191, db_index=True)),
                ('name_int', models.IntegerField(default=-1)),
            ],
            options={
                'ordering': ['-name_int'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StudentCourseMark',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('update_time', models.DateTimeField(default=django.utils.timezone.now, auto_now=True)),
                ('course', models.ForeignKey(to='courses.Course', db_index=False, on_delete=models.DO_NOTHING)),
                ('mark', models.ForeignKey(to='courses.MarkField', blank=True, null=True, db_index=False, on_delete=models.DO_NOTHING)),
                ('student', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)),
                ('teacher', models.ForeignKey(related_name='teacher_change_mark', blank=True, to=settings.AUTH_USER_MODEL, null=True, db_index=False, on_delete=models.DO_NOTHING)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='studentcoursemark',
            unique_together=set([('student', 'course')]),
        ),
        migrations.AlterUniqueTogether(
            name='defaultteacher',
            unique_together=set([('course', 'group')]),
        ),
        migrations.AddField(
            model_name='coursemarksystem',
            name='marks',
            field=models.ManyToManyField(to='courses.MarkField', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='course',
            name='filename_extensions',
            field=models.ManyToManyField(related_name='filename_extensions_set', null=True, to='courses.FilenameExtension', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='course',
            name='group_with_extern',
            field=models.ForeignKey(related_name='course_with_extern', blank=True, to='groups.Group', null=True, db_index=False, on_delete=models.DO_NOTHING),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='course',
            name='groups',
            field=models.ManyToManyField(to='groups.Group', null=True, blank=True),
            preserve_default=True,
        ),
    ]
