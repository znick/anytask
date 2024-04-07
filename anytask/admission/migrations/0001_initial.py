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
            name='AdmissionRegistrationProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('activation_key', models.CharField(max_length=40, null=True, blank=True)),
                ('old_activation_key', models.CharField(max_length=40, null=True, blank=True)),
                ('is_updating', models.BooleanField(default=False)),
                ('user_info', models.TextField(null=True, blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
