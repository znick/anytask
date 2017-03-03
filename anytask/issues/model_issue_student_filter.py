# coding: utf-8

import django_filters

from django import forms
from django.utils.translation import ugettext as _

from courses.models import Course
from issues.models import Issue
from issues.model_issue_status import IssueStatus


class IssueFilterStudent(django_filters.FilterSet):
    is_active = django_filters.ChoiceFilter(label=u'<strong>{0}</strong>'.format(_(u'Тип курса')),
                                            name='task__course__is_active')
    years = django_filters.MultipleChoiceFilter(label=u'<strong>{0}</strong>'.format(_(u'Год курса')),
                                                name='task__course__year', widget=forms.CheckboxSelectMultiple)
    courses = django_filters.MultipleChoiceFilter(label=u'<strong>{0}</strong>'.format(_(u'Курс')), name='task__course',
                                                  widget=forms.SelectMultiple)
    responsible = django_filters.MultipleChoiceFilter(label=u'<strong>{0}</strong>'.format(_(u'Преподаватели')),
                                                      widget=forms.SelectMultiple)
    status_field = django_filters.MultipleChoiceFilter(label=u'<strong>{0}</strong>'.format(_(u'Статус')),
                                                       widget=forms.SelectMultiple)
    update_time = django_filters.DateRangeFilter(label=u'<strong>{0}</strong>'.format(_(u'Дата последнего изменения')))

    def set_user(self, user):
        groups = user.group_set.all()
        courses = Course.objects.filter(groups__in=groups)

        course_choices = set()
        year_choices = set()
        teacher_set = set()
        status_set = set()
        for course in courses:
            course_choices.add((course.id, course.name))
            year_choices.add((course.year.id, unicode(course.year)))

            for teacher in course.get_teachers():
                teacher_set.add(teacher)

            for status in course.issue_status_system.statuses.all():
                status_set.add(status)

        self.filters['is_active'].field.choices = ((u'', _(u'Любой')),
                                                   (1, _(u'Активный')),
                                                   (0, _(u'Архив')))
        self.filters['years'].field.choices = tuple(year_choices)
        self.filters['courses'].field.choices = tuple(course_choices)

        teacher_choices = [(teacher.id, teacher.get_full_name()) for teacher in teacher_set]
        self.filters['responsible'].field.choices = tuple(teacher_choices)

        status_choices = [(status.id, status.name) for status in status_set]
        for status_id in sorted(IssueStatus.HIDDEN_STATUSES.values(), reverse=True):
            status_field = IssueStatus.objects.get(pk=status_id)
            status_choices.insert(0, (status_field.id, status_field.name))
        self.filters['status_field'].field.choices = tuple(status_choices)

    class Meta:
        model = Issue
        fields = ['status_field', 'responsible', 'courses', 'update_time', 'years', 'is_active']
