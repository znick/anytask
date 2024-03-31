# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mail', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='recipients_status',
            field=models.ManyToManyField(to='users.UserStatus', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='message',
            name='recipients_user',
            field=models.ManyToManyField(related_name='recipients_user+', null=True, to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='message',
            name='sender',
            field=models.ForeignKey(related_name='sender+', to=settings.AUTH_USER_MODEL, db_index=False, on_delete=models.DO_NOTHING),
            preserve_default=True,
        ),
    ]
