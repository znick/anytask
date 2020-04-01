# coding: utf-8

import django_filters
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from issues.model_issue_status import IssueStatus
from pytz import timezone as timezone_pytz
from tasks.models import Task

from issues.models import Issue


class IssueFilter(django_filters.FilterSet):
    status_field = django_filters.MultipleChoiceFilter(label=_('status'), widget=forms.SelectMultiple)
    update_time = django_filters.DateRangeFilter(label=_('data_poslednego_izmenenija'))
    responsible = django_filters.MultipleChoiceFilter(label=_('proverjaushij'), widget=forms.SelectMultiple)
    followers = django_filters.MultipleChoiceFilter(label=_('nabludateli'), widget=forms.SelectMultiple)
    students = django_filters.MultipleChoiceFilter(name="student", label=_('studenty'), widget=forms.SelectMultiple)
    seminars = django_filters.MultipleChoiceFilter(
        name="task__parent_task", label=_('uroki'), widget=forms.SelectMultiple
    )
    task = django_filters.MultipleChoiceFilter(label=_('zadacha'), widget=forms.SelectMultiple)

    def set_course(self, course, user):
        default_choices = {}
        lang = user.profile.language
        for field in self.filters:
            self.filters[field].field.label = u'<strong>{0}</strong>'.format(self.filters[field].field.label)
        teacher_choices = []

        for teacher in course.get_teachers():
            teacher_choices.append((teacher.id, teacher.get_full_name()))
            if teacher.id == user.id:
                default_choices['responsible'] = [str(teacher.id)]
        self.filters['responsible'].field.choices = tuple(teacher_choices)

        self.filters['followers'].field.choices = tuple(teacher_choices)

        students_choices = [(teacher.id, teacher.get_full_name()) for teacher in course.get_students()]
        self.filters['students'].field.choices = tuple(students_choices)

        tasks_all = Task.objects\
            .filter(course=course)\
            .exclude(type=Task.TYPE_MATERIAL)\
            .distinct()

        seminars = tasks_all.filter(type=Task.TYPE_SEMINAR)
        task_choices = [(task.id, task.get_title(lang)) for task in seminars]
        self.filters['seminars'].field.choices = tuple(task_choices)

        tasks = tasks_all.exclude(type=Task.TYPE_SEMINAR)
        task_choices = [(task.id, task.get_title(lang)) for task in tasks]
        self.filters['task'].field.choices = tuple(task_choices)

        status_choices = []
        for status in course.issue_status_system.statuses.exclude(tag=IssueStatus.STATUS_SEMINAR):
            status_choices.append((status.id, status.get_name(lang)))
            if status.tag == Issue.STATUS_VERIFICATION and default_choices:
                default_choices['status_field'] = [str(status.id)]
        for status_id in sorted(IssueStatus.HIDDEN_STATUSES.values(), reverse=True):
            status_field = IssueStatus.objects.get(pk=status_id)
            status_choices.insert(0, (status_field.id, status_field.get_name(lang)))
        self.filters['status_field'].field.choices = tuple(status_choices)

        return default_choices

    def set_data(self, data):
        self.data_full = data

    @property
    def qs(self):
        issues = super(IssueFilter, self).qs
        issues_count = len(issues)
        lang = self.data_full.get('lang', settings.LANGUAGE_CODE)
        timezone = self.data_full.get('timezone', settings.TIME_ZONE)
        start = int(self.data_full.get('start', 0))
        end = start + int(self.data_full.get('length', 50))
        data = []
        issues = issues[start:end]
        for issue in issues:
            student = issue.student
            responsible = issue.responsible
            data.append({
                "start": start,
                "has_issue_access": issue.task.has_issue_access(),
                "issue_url": issue.get_absolute_url(),
                "student_url": student.get_absolute_url(),
                "student_name": u'%s %s' % (student.last_name, student.first_name),
                "task_title": issue.task.get_title(lang),
                "update_time": issue.update_time.astimezone(timezone_pytz(timezone)).strftime('%d-%m-%Y %H:%M'),
                "mark": float(issue.score()),
                "status_name": issue.status_field.get_name(lang),
                "status_color": issue.status_field.color,
                "responsible_url": responsible.get_absolute_url() if responsible else "",
                "responsible_name": u'%s %s' % (responsible.last_name, responsible.first_name) if responsible else "",
                "DT_RowId": "row_issue_" + str(issue.id),
                "DT_RowData": {
                    "id": issue.id
                },
            })

        self.response = {
            'draw': self.data_full.get('draw', None),
            'recordsTotal': issues_count,
            'recordsFiltered': issues_count,
            'data': data,
            'url': "queue?" + self.data_full.get('filter', ''),
        }

        return Issue.objects.none()

    class Meta:
        model = Issue
        fields = ['students', 'responsible', 'followers', 'seminars', 'task', 'status_field', 'update_time']

