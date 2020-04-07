# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0001_initial'),
        ('courses', '0002_auto_20200328_1939'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=191, null=True, blank=True)),
                ('text', models.TextField(null=True, blank=True)),
                ('hidden_copy', models.BooleanField(default=False)),
                ('variable', models.BooleanField(default=False)),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True)),
                ('recipients', models.ManyToManyField(related_name=b'recipients+', to=settings.AUTH_USER_MODEL)),
                ('recipients_course', models.ManyToManyField(to='courses.Course', null=True, blank=True)),
                ('recipients_group', models.ManyToManyField(to='groups.Group', null=True, blank=True)),
            ],
            options={
                'ordering': ['-create_time'],
            },
            bases=(models.Model,),
        ),
    ]
