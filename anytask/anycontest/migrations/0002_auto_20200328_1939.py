# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issues', '0001_initial'),
        ('anycontest', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contestsubmission',
            name='file',
            field=models.ForeignKey(to='issues.File'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contestsubmission',
            name='issue',
            field=models.ForeignKey(to='issues.Issue'),
            preserve_default=True,
        ),
    ]
