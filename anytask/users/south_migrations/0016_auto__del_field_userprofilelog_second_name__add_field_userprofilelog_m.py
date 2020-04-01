# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'UserProfileLog.second_name'
        db.delete_column('users_userprofilelog', 'second_name')

        # Adding field 'UserProfileLog.middle_name'
        db.add_column('users_userprofilelog', 'middle_name',
                      self.gf('django.db.models.fields.CharField')(db_index=True, max_length=128, null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfileLog.phone'
        db.add_column('users_userprofilelog', 'phone',
                      self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfileLog.city_of_residence'
        db.add_column('users_userprofilelog', 'city_of_residence',
                      self.gf('django.db.models.fields.CharField')(max_length=191, null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfileLog.university'
        db.add_column('users_userprofilelog', 'university',
                      self.gf('django.db.models.fields.CharField')(max_length=191, null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfileLog.university_in_process'
        db.add_column('users_userprofilelog', 'university_in_process',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'UserProfileLog.university_class'
        db.add_column('users_userprofilelog', 'university_class',
                      self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfileLog.university_department'
        db.add_column('users_userprofilelog', 'university_department',
                      self.gf('django.db.models.fields.CharField')(max_length=191, null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfileLog.university_year_end'
        db.add_column('users_userprofilelog', 'university_year_end',
                      self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfileLog.additional_info'
        db.add_column('users_userprofilelog', 'additional_info',
                      self.gf('django.db.models.fields.TextField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfileLog.login_via_yandex'
        db.add_column('users_userprofilelog', 'login_via_yandex',
                      self.gf('django.db.models.fields.BooleanField')(default=True),
                      keep_default=False)

        # Adding field 'UserProfileLog.ya_contest_uid'
        db.add_column('users_userprofilelog', 'ya_contest_uid',
                      self.gf('django.db.models.fields.IntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfileLog.ya_contest_login'
        db.add_column('users_userprofilelog', 'ya_contest_login',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=128, null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfileLog.ya_passport_uid'
        db.add_column('users_userprofilelog', 'ya_passport_uid',
                      self.gf('django.db.models.fields.IntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfileLog.ya_passport_login'
        db.add_column('users_userprofilelog', 'ya_passport_login',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=128, null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfileLog.ya_passport_email'
        db.add_column('users_userprofilelog', 'ya_passport_email',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=128, null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserProfileLog.language'
        db.add_column('users_userprofilelog', 'language',
                      self.gf('django.db.models.fields.CharField')(default='ru', max_length=128, null=True, blank=True),
                      keep_default=False)

        # Adding M2M table for field unread_messages on 'UserProfileLog'
        m2m_table_name = db.shorten_name('users_userprofilelog_unread_messages')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofilelog', models.ForeignKey(orm['users.userprofilelog'], null=False)),
            ('message', models.ForeignKey(orm['mail.message'], null=False))
        ))
        db.create_unique(m2m_table_name, ['userprofilelog_id', 'message_id'])

        # Adding M2M table for field deleted_messages on 'UserProfileLog'
        m2m_table_name = db.shorten_name('users_userprofilelog_deleted_messages')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofilelog', models.ForeignKey(orm['users.userprofilelog'], null=False)),
            ('message', models.ForeignKey(orm['mail.message'], null=False))
        ))
        db.create_unique(m2m_table_name, ['userprofilelog_id', 'message_id'])

        # Adding M2M table for field send_notify_messages on 'UserProfileLog'
        m2m_table_name = db.shorten_name('users_userprofilelog_send_notify_messages')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofilelog', models.ForeignKey(orm['users.userprofilelog'], null=False)),
            ('message', models.ForeignKey(orm['mail.message'], null=False))
        ))
        db.create_unique(m2m_table_name, ['userprofilelog_id', 'message_id'])


    def backwards(self, orm):
        # Adding field 'UserProfileLog.second_name'
        db.add_column('users_userprofilelog', 'second_name',
                      self.gf('django.db.models.fields.CharField')(blank=True, max_length=128, null=True, db_index=True),
                      keep_default=False)

        # Deleting field 'UserProfileLog.middle_name'
        db.delete_column('users_userprofilelog', 'middle_name')

        # Deleting field 'UserProfileLog.phone'
        db.delete_column('users_userprofilelog', 'phone')

        # Deleting field 'UserProfileLog.city_of_residence'
        db.delete_column('users_userprofilelog', 'city_of_residence')

        # Deleting field 'UserProfileLog.university'
        db.delete_column('users_userprofilelog', 'university')

        # Deleting field 'UserProfileLog.university_in_process'
        db.delete_column('users_userprofilelog', 'university_in_process')

        # Deleting field 'UserProfileLog.university_class'
        db.delete_column('users_userprofilelog', 'university_class')

        # Deleting field 'UserProfileLog.university_department'
        db.delete_column('users_userprofilelog', 'university_department')

        # Deleting field 'UserProfileLog.university_year_end'
        db.delete_column('users_userprofilelog', 'university_year_end')

        # Deleting field 'UserProfileLog.additional_info'
        db.delete_column('users_userprofilelog', 'additional_info')

        # Deleting field 'UserProfileLog.login_via_yandex'
        db.delete_column('users_userprofilelog', 'login_via_yandex')

        # Deleting field 'UserProfileLog.ya_contest_uid'
        db.delete_column('users_userprofilelog', 'ya_contest_uid')

        # Deleting field 'UserProfileLog.ya_contest_login'
        db.delete_column('users_userprofilelog', 'ya_contest_login')

        # Deleting field 'UserProfileLog.ya_passport_uid'
        db.delete_column('users_userprofilelog', 'ya_passport_uid')

        # Deleting field 'UserProfileLog.ya_passport_login'
        db.delete_column('users_userprofilelog', 'ya_passport_login')

        # Deleting field 'UserProfileLog.ya_passport_email'
        db.delete_column('users_userprofilelog', 'ya_passport_email')

        # Deleting field 'UserProfileLog.language'
        db.delete_column('users_userprofilelog', 'language')

        # Removing M2M table for field unread_messages on 'UserProfileLog'
        db.delete_table(db.shorten_name('users_userprofilelog_unread_messages'))

        # Removing M2M table for field deleted_messages on 'UserProfileLog'
        db.delete_table(db.shorten_name('users_userprofilelog_deleted_messages'))

        # Removing M2M table for field send_notify_messages on 'UserProfileLog'
        db.delete_table(db.shorten_name('users_userprofilelog_send_notify_messages'))


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'courses.course': {
            'Meta': {'object_name': 'Course'},
            'added_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'can_be_chosen_by_extern': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'contest_integrated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'default_accepted_after_contest_ok': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'default_task_one_file_upload': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'filename_extensions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'filename_extensions_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['courses.FilenameExtension']"}),
            'full_transcript': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'group_with_extern': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'course_with_extern'", 'null': 'True', 'db_index': 'False', 'to': "orm['groups.Group']"}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['groups.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'information': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'issue_fields': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['issues.IssueField']", 'null': 'True', 'blank': 'True'}),
            'issue_status_system': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'to': "orm['issues.IssueStatusSystem']", 'db_index': 'False'}),
            'mark_system': ('django.db.models.fields.related.ForeignKey', [], {'db_index': 'False', 'to': "orm['courses.CourseMarkSystem']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '191', 'db_index': 'True'}),
            'name_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '191', 'null': 'True', 'blank': 'True'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'rb_integrated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'send_rb_and_contest_together': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'send_to_contest_from_users': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'show_accepted_after_contest_ok': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'show_task_one_file_upload': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'teachers': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'course_teachers_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'year': ('django.db.models.fields.related.ForeignKey', [], {'default': '2017', 'to': "orm['years.Year']"})
        },
        'courses.coursemarksystem': {
            'Meta': {'object_name': 'CourseMarkSystem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marks': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['courses.MarkField']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '191'})
        },
        'courses.filenameextension': {
            'Meta': {'object_name': 'FilenameExtension'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'courses.markfield': {
            'Meta': {'object_name': 'MarkField'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '191', 'db_index': 'True'}),
            'name_int': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'groups.group': {
            'Meta': {'unique_together': "(('year', 'name'),)", 'object_name': 'Group'},
            'added_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '191', 'blank': 'True'}),
            'students': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'year': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['years.Year']", 'blank': 'True'})
        },
        'issues.issuefield': {
            'Meta': {'object_name': 'IssueField'},
            'history_message': ('django.db.models.fields.CharField', [], {'max_length': '191', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '191'}),
            'plugin': ('django.db.models.fields.CharField', [], {'default': "'FieldDefaultPlugin'", 'max_length': '191'}),
            'plugin_version': ('django.db.models.fields.CharField', [], {'default': "'0.1'", 'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '191', 'blank': 'True'})
        },
        'issues.issuestatus': {
            'Meta': {'object_name': 'IssueStatus'},
            'color': ('colorfield.fields.ColorField', [], {'default': "'#818A91'", 'max_length': '10'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '191', 'db_index': 'True'}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '191', 'null': 'True', 'blank': 'True'})
        },
        'issues.issuestatussystem': {
            'Meta': {'object_name': 'IssueStatusSystem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '191'}),
            'statuses': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['issues.IssueStatus']", 'null': 'True', 'blank': 'True'})
        },
        'mail.message': {
            'Meta': {'ordering': "['-create_time']", 'object_name': 'Message'},
            'create_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recipients': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'recipients+'", 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'recipients_course': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['courses.Course']", 'null': 'True', 'blank': 'True'}),
            'recipients_group': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['groups.Group']", 'null': 'True', 'blank': 'True'}),
            'recipients_user': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'recipients_user+'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sender+'", 'db_index': 'False', 'to': "orm['auth.User']"}),
            'text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '191', 'null': 'True', 'blank': 'True'})
        },
        'users.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'academic_degree': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'academic_title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'added_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'additional_info': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'birth_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'city_of_residence': ('django.db.models.fields.CharField', [], {'max_length': '191', 'null': 'True', 'blank': 'True'}),
            'deleted_messages': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'deleted_messages'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['mail.Message']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'ru'", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'login_via_yandex': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'position': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'send_my_own_events': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'send_notify_messages': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'send_notify_messages'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['mail.Message']"}),
            'show_email': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'unit': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'university': ('django.db.models.fields.CharField', [], {'max_length': '191', 'null': 'True', 'blank': 'True'}),
            'university_class': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'university_department': ('django.db.models.fields.CharField', [], {'max_length': '191', 'null': 'True', 'blank': 'True'}),
            'university_in_process': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'university_year_end': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'unread_messages': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'unread_messages'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['mail.Message']"}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'updated_by': ('django.db.models.fields.related.ForeignKey', [], {'db_index': 'False', 'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'profile'", 'unique': 'True', 'to': "orm['auth.User']"}),
            'user_status': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'users_by_status'", 'to': "orm['users.UserStatus']", 'blank': 'True', 'symmetrical': 'False', 'null': 'True', 'db_index': 'True'}),
            'ya_contest_login': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ya_contest_oauth': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ya_contest_uid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ya_login': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ya_passport_email': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ya_passport_login': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ya_passport_oauth': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ya_passport_uid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ya_uid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'users.userprofilelog': {
            'Meta': {'object_name': 'UserProfileLog'},
            'academic_degree': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'academic_title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'added_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'additional_info': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'birth_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'city_of_residence': ('django.db.models.fields.CharField', [], {'max_length': '191', 'null': 'True', 'blank': 'True'}),
            'deleted_messages': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'log_deleted_messages'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['mail.Message']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'ru'", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'login_via_yandex': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'position': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'send_my_own_events': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'send_notify_messages': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'log_send_notify_messages'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['mail.Message']"}),
            'show_email': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'unit': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'university': ('django.db.models.fields.CharField', [], {'max_length': '191', 'null': 'True', 'blank': 'True'}),
            'university_class': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'university_department': ('django.db.models.fields.CharField', [], {'max_length': '191', 'null': 'True', 'blank': 'True'}),
            'university_in_process': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'university_year_end': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'unread_messages': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'log_unread_messages'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['mail.Message']"}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'updated_by': ('django.db.models.fields.related.ForeignKey', [], {'db_index': 'False', 'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'profiles_logs_by_user'", 'to': "orm['auth.User']"}),
            'user_status': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['users.UserStatus']", 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'ya_contest_login': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ya_contest_oauth': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ya_contest_uid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ya_login': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ya_passport_email': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ya_passport_login': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ya_passport_oauth': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'ya_passport_uid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ya_uid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'users.userstatus': {
            'Meta': {'object_name': 'UserStatus'},
            'color': ('colorfield.fields.ColorField', [], {'default': "'#818A91'", 'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '254', 'db_index': 'True'}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '254', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '191', 'null': 'True', 'blank': 'True'})
        },
        'years.year': {
            'Meta': {'object_name': 'Year'},
            'added_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_year': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['users']