# -*- coding: utf-8 -*-
from django.core.management import call_command
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Don't use "from appname.models import ModelName". 
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications.

        # pk 1
        orm.IssueField(**{'history_message': '',
                          'plugin_version': '0.1',
                          'name': 'comment',
                          'plugin': 'FieldCommentPlugin',
                          'title': u'Комментарий'}).save()
        # pk 2
        orm.IssueField(**{'history_message': '',
                          'plugin_version': '0.1',
                          'name': 'course_name',
                          'plugin': 'FieldReadOnlyPlugin',
                          'title': u'Предмет'}).save()
        # pk 3
        orm.IssueField(**{'history_message': '',
                          'plugin_version': '0.1',
                          'name': 'task_name',
                          'plugin': 'FieldReadOnlyPlugin',
                          'title': u'Задача'}).save()
        # pk 4
        orm.IssueField(**{'history_message': '',
                          'plugin_version': '0.1',
                          'name': 'student_name',
                          'plugin': 'FieldReadOnlyPlugin',
                          'title': u'Студент'}).save()
        # pk 5
        orm.IssueField(**{'history_message': u'Теперь задачу проверяет',
                          'plugin_version': '0.1',
                          'name': 'responsible_name',
                          'plugin': 'FieldResponsiblePlugin',
                          'title': u'Проверяющий'}).save()
        # pk 6
        orm.IssueField(**{'history_message': u'За задачей наблюдают:',
                          'plugin_version': '0.1',
                          'name': 'followers_names',
                          'plugin': 'FieldFollowersPlugin',
                          'title': u'Наблюдатели'}).save()
        # pk 7
        orm.IssueField(**{'history_message': u'Статус изменен:',
                          'plugin_version': '0.1',
                          'name': 'status',
                          'plugin': 'FieldStatusPlugin',
                          'title': u'Статус'}).save()
        # pk 8
        orm.IssueField(**{'history_message': u'Оценка изменена на',
                          'plugin_version': '0.1',
                          'name': 'mark',
                          'plugin': 'FieldMarkPlugin',
                          'title': u'Оценка'}).save()
        # pk 9
        orm.IssueField(**{'history_message': u'Загружен файл:',
                          'plugin_version': '0.1',
                          'name': 'file',
                          'plugin': 'FieldFilePlugin',
                          'title': u'Файл'}).save()
        # pk 10
        orm.IssueField(**{'history_message': '',
                          'plugin_version': '0.1',
                          'name': 'review_id',
                          'plugin': 'FieldReadOnlyPlugin',
                          'title': u'Номер ревью'}).save()
        # pk 11
        orm.IssueField(**{'history_message': '',
                          'plugin_version': '0.1',
                          'name': 'run_id',
                          'plugin': 'FieldReadOnlyPlugin',
                          'title': u'Номер посылки в контест'}).save()


    def backwards(self, orm):
        "Write your backwards methods here."

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
            'days_drop_from_blacklist': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'filename_extensions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'filename_extensions_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['courses.FilenameExtension']"}),
            'full_transcript': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'gr_integrated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['groups.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'information': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'issue_fields': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['issues.IssueField']", 'symmetrical': 'False'}),
            'max_days_without_score': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'max_tasks_without_score_per_student': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'max_users_per_task': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '254', 'db_index': 'True'}),
            'name_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '254', 'null': 'True', 'blank': 'True'}),
            'pdf_integrated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rb_integrated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'students': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'course_students_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'take_policy': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '1', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'teachers': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'course_teachers_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'type': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '1', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'year': ('django.db.models.fields.related.ForeignKey', [], {'default': '2014', 'to': "orm['years.Year']"})
        },
        'courses.filenameextension': {
            'Meta': {'object_name': 'FilenameExtension'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10'})
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
        'issues.event': {
            'Meta': {'object_name': 'Event'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'field': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'to': "orm['issues.IssueField']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['issues.Issue']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'max_length': '2500', 'blank': 'True'})
        },
        'issues.file': {
            'Meta': {'object_name': 'File'},
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['issues.Event']"}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'issues.issue': {
            'Meta': {'object_name': 'Issue'},
            'create_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'followers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'responsible': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'responsible'", 'null': 'True', 'to': "orm['auth.User']"}),
            'student': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'student'", 'to': "orm['auth.User']"}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['tasks.Task']", 'null': 'True'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
        },
        'issues.issuefield': {
            'Meta': {'object_name': 'IssueField'},
            'history_message': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'plugin': ('django.db.models.fields.CharField', [], {'default': "'DefaultPlugin'", 'max_length': '250'}),
            'plugin_version': ('django.db.models.fields.CharField', [], {'default': "'0.1'", 'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'})
        },
        'tasks.task': {
            'Meta': {'object_name': 'Task'},
            'added_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['courses.Course']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['groups.Group']", 'null': 'True', 'db_index': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'parent_task': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'parent_task_set'", 'null': 'True', 'to': "orm['tasks.Task']"}),
            'score_max': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'task_text': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '254', 'null': 'True', 'blank': 'True'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'updated_by': ('django.db.models.fields.related.ForeignKey', [], {'db_index': 'False', 'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'weight': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'})
        },
        'years.year': {
            'Meta': {'object_name': 'Year'},
            'added_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_year': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['issues']
    symmetrical = True
