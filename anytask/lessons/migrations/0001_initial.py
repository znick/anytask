# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0001_initial'),
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100, null=True, blank=True)),
                ('description', models.TextField(default='', null=True, blank=True)),
                ('date_starttime', models.DateTimeField(default=None, null=True)),
                ('date_endtime', models.DateTimeField(default=None, null=True)),
                ('schedule_id', models.CharField(db_index=True, max_length=100, null=True, blank=True)),
                ('position', models.IntegerField(db_index=True, null=True, blank=True)),
                ('period', models.CharField(default='Once', max_length=128, choices=[('Once', 'odin_raz'), ('Weekly', 'ezhenedelno')])),
                ('date_end', models.DateTimeField(default=None, null=True)),
                ('days', models.CharField(db_index=True, max_length=100, null=True, blank=True)),
                ('course', models.ForeignKey(to='courses.Course', on_delete=models.DO_NOTHING)),
                ('group', models.ForeignKey(to='groups.Group', on_delete=models.DO_NOTHING)),
                ('not_visited_students', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, blank=True)),
                ('updated_by', models.ForeignKey(related_name='authors', blank=True, to=settings.AUTH_USER_MODEL, null=True, db_index=False, on_delete=models.DO_NOTHING)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
