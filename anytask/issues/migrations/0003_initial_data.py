# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def add_data_to_issue_status(apps, schema_editor):
    IssueField = apps.get_model('issues', 'IssueField')

    # pk 1
    IssueField(**{'history_message': '',
                  'plugin_version': '0.1',
                  'name': 'comment',
                  'plugin': 'FieldCommentPlugin',
                  'title': u'Комментарий'}).save()

    # pk 2
    IssueField(**{'history_message': '',
                      'plugin_version': '0.1',
                      'name': 'course_name',
                      'plugin': 'FieldReadOnlyPlugin',
                      'title': u'Предмет'}).save()
    # pk 3
    IssueField(**{'history_message': '',
                      'plugin_version': '0.1',
                      'name': 'task_name',
                      'plugin': 'FieldReadOnlyPlugin',
                      'title': u'Задача'}).save()
    # pk 4
    IssueField(**{'history_message': '',
                      'plugin_version': '0.1',
                      'name': 'student_name',
                      'plugin': 'FieldReadOnlyPlugin',
                      'title': u'Студент'}).save()
    # pk 5
    IssueField(**{'history_message': u'Теперь задачу проверяет',
                      'plugin_version': '0.1',
                      'name': 'responsible_name',
                      'plugin': 'FieldResponsiblePlugin',
                      'title': u'Проверяющий'}).save()
    # pk 6
    IssueField(**{'history_message': u'За задачей наблюдают:',
                      'plugin_version': '0.1',
                      'name': 'followers_names',
                      'plugin': 'FieldFollowersPlugin',
                      'title': u'Наблюдатели'}).save()
    # pk 7
    IssueField(**{'history_message': u'Статус изменен:',
                      'plugin_version': '0.1',
                      'name': 'status',
                      'plugin': 'FieldStatusPlugin',
                      'title': u'Статус'}).save()
    # pk 8
    IssueField(**{'history_message': u'Оценка изменена на',
                      'plugin_version': '0.1',
                      'name': 'mark',
                      'plugin': 'FieldMarkPlugin',
                      'title': u'Оценка'}).save()
    # pk 9
    IssueField(**{'history_message': u'Загружен файл:',
                      'plugin_version': '0.1',
                      'name': 'file',
                      'plugin': 'FieldFilePlugin',
                      'title': u'Файл'}).save()
    # pk 10
    IssueField(**{'history_message': '',
                      'plugin_version': '0.1',
                      'name': 'review_id',
                      'plugin': 'FieldReadOnlyPlugin',
                      'title': u'Номер ревью'}).save()
    # pk 11
    IssueField(**{'history_message': '',
                      'plugin_version': '0.1',
                      'name': 'run_id',
                      'plugin': 'FieldReadOnlyPlugin',
                      'title': u'Номер посылки в контест'}).save()

    # pk 12
    IssueField(**{'history_message': 'Студенты:',
                      'plugin_version': '0.1',
                      'name': 'costudents_names',
                      'plugin': 'FieldCostudentsPlugin',
                      'title': u'Номер посылки в контест'}).save()


class Migration(migrations.Migration):

    dependencies = [
        ('issues', '0002_auto_20200328_1939'),
    ]

    operations = [
        migrations.RunPython(add_data_to_issue_status)
    ]
