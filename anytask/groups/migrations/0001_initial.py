# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('years', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(db_index=True, max_length=191, blank=True)),
                ('added_time', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True)),
                ('update_time', models.DateTimeField(default=django.utils.timezone.now, auto_now=True)),
                ('students', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, blank=True)),
                ('year', models.ForeignKey(to='years.Year', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='group',
            unique_together=set([('year', 'name')]),
        ),
    ]
