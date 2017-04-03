# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Course.default_task_send_to_users'
        db.add_column('courses_course', 'default_task_send_to_users',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Course.default_task_send_to_users'
        db.delete_column('courses_course', 'default_task_send_to_users')


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
            'default_task_send_to_users': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'year': ('django.db.models.fields.related.ForeignKey', [], {'default': '2016', 'to': "orm['years.Year']"})
        },
        'courses.coursemarksystem': {
            'Meta': {'object_name': 'CourseMarkSystem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marks': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['courses.MarkField']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '191'})
        },
        'courses.defaultteacher': {
            'Meta': {'unique_together': "(('course', 'group'),)", 'object_name': 'DefaultTeacher'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['courses.Course']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['groups.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'teacher': ('django.db.models.fields.related.ForeignKey', [], {'db_index': 'False', 'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
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
        'courses.studentcoursemark': {
            'Meta': {'unique_together': "(('student', 'course'),)", 'object_name': 'StudentCourseMark'},
            'course': (
            'django.db.models.fields.related.ForeignKey', [], {'to': "orm['courses.Course']", 'db_index': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mark': ('django.db.models.fields.related.ForeignKey', [],
                     {'db_index': 'False', 'to': "orm['courses.MarkField']", 'null': 'True', 'blank': 'True'}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'teacher': ('django.db.models.fields.related.ForeignKey', [],
                        {'blank': 'True', 'related_name': "'teacher_change_mark'", 'null': 'True', 'db_index': 'False',
                         'to': "orm['auth.User']"}),
            'update_time': ('django.db.models.fields.DateTimeField', [],
                            {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
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
        'years.year': {
            'Meta': {'object_name': 'Year'},
            'added_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_year': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['courses']