# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2023-02-24 17:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lessons', '0002_auto_20210228_1721'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lesson',
            name='period',
            field=models.CharField(choices=[(b'Once', '\u043e\u0434\u0438\u043d \u0440\u0430\u0437'), (b'Weekly', '\u043a\u0430\u0436\u0434\u0443\u044e \u043d\u0435\u0434\u0435\u043b\u044e')], default=b'Once', max_length=128),
        ),
    ]
