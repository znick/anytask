# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import users.models
import anytask.storage
import colorfield.fields
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mail', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('middle_name', models.CharField(db_index=True, max_length=128, null=True, blank=True)),
                ('avatar', models.ImageField(storage=anytask.storage.OverwriteStorage(), upload_to=users.models.get_upload_path, null=True, verbose_name='profile picture', blank=True)),
                ('birth_date', models.DateField(null=True, blank=True)),
                ('info', models.TextField(default='', null=True, blank=True)),
                ('phone', models.CharField(max_length=128, null=True, blank=True)),
                ('city_of_residence', models.CharField(max_length=191, null=True, blank=True)),
                ('university', models.CharField(max_length=191, null=True, blank=True)),
                ('university_in_process', models.BooleanField(default=False)),
                ('university_class', models.CharField(max_length=191, null=True, blank=True)),
                ('university_department', models.CharField(max_length=191, null=True, blank=True)),
                ('university_year_end', models.CharField(max_length=191, null=True, blank=True)),
                ('additional_info', models.TextField(null=True, blank=True)),
                ('unit', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('position', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('academic_degree', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('academic_title', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('show_email', models.BooleanField(default=True)),
                ('send_my_own_events', models.BooleanField(default=False)),
                ('added_time', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True)),
                ('update_time', models.DateTimeField(default=django.utils.timezone.now, auto_now=True)),
                ('login_via_yandex', models.BooleanField(default=False)),
                ('ya_uid', models.IntegerField(null=True, blank=True)),
                ('ya_login', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('ya_contest_uid', models.CharField(max_length=191, null=True, blank=True)),
                ('ya_contest_oauth', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('ya_contest_login', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('ya_passport_uid', models.CharField(max_length=191, null=True, blank=True)),
                ('ya_passport_oauth', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('ya_passport_login', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('ya_passport_email', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('language', models.CharField(default='ru', max_length=128, null=True, blank=True)),
                ('time_zone', models.TextField(default='Europe/Moscow')),
                ('location', models.TextField(default='', null=True, blank=True)),
                ('deleted_messages', models.ManyToManyField(related_name='deleted_messages', null=True, to='mail.Message', blank=True)),
                ('send_notify_messages', models.ManyToManyField(related_name='send_notify_messages', null=True, to='mail.Message', blank=True)),
                ('unread_messages', models.ManyToManyField(related_name='unread_messages', null=True, to='mail.Message', blank=True)),
                ('updated_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True, null=True, db_index=False, on_delete=models.DO_NOTHING)),
                ('user', models.OneToOneField(related_name='profile', to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfileLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('middle_name', models.CharField(db_index=True, max_length=128, null=True, blank=True)),
                ('avatar', models.ImageField(storage=anytask.storage.OverwriteStorage(), upload_to=users.models.get_upload_path, null=True, verbose_name='profile picture', blank=True)),
                ('birth_date', models.DateField(null=True, blank=True)),
                ('info', models.TextField(default='', null=True, blank=True)),
                ('phone', models.CharField(max_length=128, null=True, blank=True)),
                ('city_of_residence', models.CharField(max_length=191, null=True, blank=True)),
                ('university', models.CharField(max_length=191, null=True, blank=True)),
                ('university_in_process', models.BooleanField(default=False)),
                ('university_class', models.CharField(max_length=50, null=True, blank=True)),
                ('university_department', models.CharField(max_length=191, null=True, blank=True)),
                ('university_year_end', models.CharField(max_length=20, null=True, blank=True)),
                ('additional_info', models.TextField(null=True, blank=True)),
                ('unit', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('position', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('academic_degree', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('academic_title', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('show_email', models.BooleanField(default=True)),
                ('send_my_own_events', models.BooleanField(default=False)),
                ('added_time', models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True)),
                ('update_time', models.DateTimeField(default=django.utils.timezone.now, auto_now=True)),
                ('login_via_yandex', models.BooleanField(default=True)),
                ('ya_uid', models.IntegerField(null=True, blank=True)),
                ('ya_login', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('ya_contest_uid', models.IntegerField(null=True, blank=True)),
                ('ya_contest_oauth', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('ya_contest_login', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('ya_passport_uid', models.IntegerField(null=True, blank=True)),
                ('ya_passport_oauth', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('ya_passport_login', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('ya_passport_email', models.CharField(default='', max_length=128, null=True, blank=True)),
                ('language', models.CharField(default='ru', max_length=128, null=True, blank=True)),
                ('deleted_messages', models.ManyToManyField(related_name='log_deleted_messages', null=True, to='mail.Message', blank=True)),
                ('send_notify_messages', models.ManyToManyField(related_name='log_send_notify_messages', null=True, to='mail.Message', blank=True)),
                ('unread_messages', models.ManyToManyField(related_name='log_unread_messages', null=True, to='mail.Message', blank=True)),
                ('updated_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True, null=True, db_index=False, on_delete=models.DO_NOTHING)),
                ('user', models.ForeignKey(related_name='profiles_logs_by_user', to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=254, db_index=True)),
                ('type', models.CharField(blank=True, max_length=191, null=True, choices=[('activity', 'status_studenta'), ('filial', 'filial'), ('admission', 'status_postupleniya')])),
                ('tag', models.CharField(blank=True, max_length=254, null=True, choices=[('active', 'active'), ('extramural', 'extramural'), ('fulltime', 'fulltime'), ('not_active', 'not_active'), ('academic', 'academic')])),
                ('color', colorfield.fields.ColorField(default='#818A91', max_length=18)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='userprofilelog',
            name='user_status',
            field=models.ManyToManyField(db_index=True, to='users.UserStatus', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='user_status',
            field=models.ManyToManyField(db_index=True, related_name='users_by_status', null=True, to='users.UserStatus', blank=True),
            preserve_default=True,
        ),
    ]
