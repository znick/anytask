# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Task.contest_integrated'
        db.add_column('tasks_task', 'contest_integrated',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Task.rb_integrated'
        db.add_column('tasks_task', 'rb_integrated',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'TaskLog.contest_integrated'
        db.add_column('tasks_tasklog', 'contest_integrated',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'TaskLog.rb_integrated'
        db.add_column('tasks_tasklog', 'rb_integrated',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'TaskLog.type'
        db.add_column('tasks_tasklog', 'type',
                      self.gf('django.db.models.fields.CharField')(default='All', max_length=128),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Task.contest_integrated'
        db.delete_column('tasks_task', 'contest_integrated')

        # Deleting field 'Task.rb_integrated'
        db.delete_column('tasks_task', 'rb_integrated')

        # Deleting field 'TaskLog.contest_integrated'
        db.delete_column('tasks_tasklog', 'contest_integrated')

        # Deleting field 'TaskLog.rb_integrated'
        db.delete_column('tasks_tasklog', 'rb_integrated')

        # Deleting field 'TaskLog.type'
        db.delete_column('tasks_tasklog', 'type')


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
            'filename_extensions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'filename_extensions_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['courses.FilenameExtension']"}),
            'full_transcript': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'group_with_extern': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'course_with_extern'", 'null': 'True', 'db_index': 'False', 'to': "orm['groups.Group']"}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['groups.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'information': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'issue_fields': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['issues.IssueField']", 'null': 'True', 'blank': 'True'}),
            'mark_system': ('django.db.models.fields.related.ForeignKey', [], {'db_index': 'False', 'to': "orm['courses.CourseMarkSystem']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '254', 'db_index': 'True'}),
            'name_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '254', 'null': 'True', 'blank': 'True'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rb_integrated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'send_rb_and_contest_together': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'send_to_contest_from_users': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'teachers': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'course_teachers_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'year': ('django.db.models.fields.related.ForeignKey', [], {'default': '2016', 'to': "orm['years.Year']"})
        },
        'courses.coursemarksystem': {
            'Meta': {'object_name': 'CourseMarkSystem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marks': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['courses.MarkField']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '254'})
        },
        'courses.filenameextension': {
            'Meta': {'object_name': 'FilenameExtension'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'courses.markfield': {
            'Meta': {'object_name': 'MarkField'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '254', 'db_index': 'True'}),
            'name_int': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'groups.group': {
            'Meta': {'unique_together': "(('year', 'name'),)", 'object_name': 'Group'},
            'added_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '254', 'blank': 'True'}),
            'students': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'year': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['years.Year']", 'blank': 'True'})
        },
        'issues.issuefield': {
            'Meta': {'object_name': 'IssueField'},
            'history_message': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'plugin': ('django.db.models.fields.CharField', [], {'default': "'FieldDefaultPlugin'", 'max_length': '250'}),
            'plugin_version': ('django.db.models.fields.CharField', [], {'default': "'0.1'", 'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'})
        },
        'tasks.task': {
            'Meta': {'object_name': 'Task'},
            'added_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'contest_id': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'contest_integrated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['courses.Course']"}),
            'deadline_time': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['groups.Group']", 'null': 'True', 'db_index': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'parent_task': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'parent_task_set'", 'null': 'True', 'to': "orm['tasks.Task']"}),
            'problem_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'rb_integrated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'score_max': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'sended_notify': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'task_text': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '254', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'All'", 'max_length': '128'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'updated_by': ('django.db.models.fields.related.ForeignKey', [], {'db_index': 'False', 'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'})
        },
        'tasks.tasklog': {
            'Meta': {'object_name': 'TaskLog'},
            'added_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'contest_id': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'contest_integrated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['courses.Course']", 'db_index': 'False'}),
            'deadline_time': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['groups.Group']", 'null': 'True', 'db_index': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent_task': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'parent_task_set'", 'null': 'True', 'to': "orm['tasks.TaskLog']"}),
            'problem_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'rb_integrated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'score_max': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'task_text': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '254', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'All'", 'max_length': '128'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'updated_by': ('django.db.models.fields.related.ForeignKey', [], {'db_index': 'False', 'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'tasks.tasktaken': {
            'Meta': {'unique_together': "(('user', 'task'),)", 'object_name': 'TaskTaken'},
            'added_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'gr_review_update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'id_issue_gr_review': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'db_index': 'True'}),
            'pdf': ('django.db.models.fields.files.FileField', [], {'default': 'None', 'max_length': '100', 'null': 'True', 'db_index': 'True'}),
            'pdf_update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'score': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'scored_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'task_taken_scored_by_set'", 'null': 'True', 'to': "orm['auth.User']"}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '1', 'db_index': 'True'}),
            'status_check': ('django.db.models.fields.CharField', [], {'default': "'EDIT'", 'max_length': '5', 'db_index': 'True'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tasks.Task']"}),
            'teacher': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'teacher'", 'null': 'True', 'to': "orm['auth.User']"}),
            'teacher_comments': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'tasks.tasktakenlog': {
            'Meta': {'object_name': 'TaskTakenLog'},
            'added_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'scored_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'task_taken_log_scored_by_set'", 'null': 'True', 'db_index': 'False', 'to': "orm['auth.User']"}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '1', 'db_index': 'True'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tasks.Task']", 'db_index': 'False'}),
            'teacher_comments': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'db_index': 'False'})
        },
        'years.year': {
            'Meta': {'object_name': 'Year'},
            'added_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_year': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['tasks']