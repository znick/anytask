# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-03-19 20:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_auto_20210228_1721'),
    ]

    operations = [
        migrations.CreateModel(
            name='EasyCIRequesites',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('host', models.CharField(max_length=191)),
                ('repo', models.CharField(max_length=191)),
                ('docker_image', models.CharField(max_length=191)),
                ('timeout', models.IntegerField()),
            ],
        ),
        migrations.AddField(
            model_name='course',
            name='easyCI_integrated',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='courses.EasyCIRequesites'),
        ),
    ]
