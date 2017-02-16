# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _

from django.db import models
from django.contrib.auth.models import User
from courses.models import Course
from groups.models import Group
from users.models import UserProfile, UserStatus
from issues.models import Issue
from django import forms


import django_filters

# def get_user_sum_score(user, course, group):
#     issues = Issue.objects.filter(task__in=group_x_task_list[group]).filter(
#         student__group__in=[group]).order_by('student').select_related()
#
#     from collections import defaultdict
#     issues_x_student = defaultdict(list)
#     for issue in issues_students_in_group.all():
#         student_id = issue.student.id
#         issues_x_student[student_id].append(issue)
#
#     for student in group.students.filter(is_active=True):
#         if user == student:
#             user_is_attended = True
#             user_is_attended_special_course = True
#
#         student_task_takens = issues_x_student[student.id]
#
#         task_x_task_taken = {}
#         student_summ_scores = 0
#         for task_taken in student_task_takens:
#             task_x_task_taken[task_taken.task.id] = task_taken
#             if not task_taken.task.is_hidden:
#                 student_summ_scores += task_taken.mark
#
#         student_x_task_x_task_takens[student] = (task_x_task_taken, student_summ_scores)
#
#     group_x_student_x_task_takens[group] = student_x_task_x_task_takens


class CustomMethodFilter(django_filters.MethodFilter):
    def __init__(self, *args, **kwargs):
        self.field_class = kwargs.pop('field_class', forms.Field)

        super(CustomMethodFilter, self).__init__(*args, **kwargs)


class UserProfileFilter(django_filters.FilterSet):
    courses = CustomMethodFilter(label=u'<strong>{0}</strong>'.format(_(u'Курс')),
                                 action='filter_course',
                                 widget=forms.SelectMultiple,
                                 field_class=forms.MultipleChoiceField)
    groups = CustomMethodFilter(label=u'<strong>{0}</strong>'.format(_(u'Группа')),
                                action='filter_group',
                                widget=forms.SelectMultiple,
                                field_class=forms.MultipleChoiceField)
    user_status = django_filters.MultipleChoiceFilter(label=u'<strong>{0}</strong>'.format(_(u'Статус студента')),
                                                      name='user_status',
                                                      widget=forms.SelectMultiple)
    sum_score = CustomMethodFilter(label=u'<strong>{0}</strong>'.format(_(u'Суммарный балл')),
                                   action='filter_sum_score',
                                   field_class=django_filters.fields.RangeField)

    # range_f = django_filters.RangeFilter()
    # user_status_education_form = django_filters.ChoiceFilter(label=_(u'<strong>Форма обучения</strong>'), name='user_status')

    @property
    def qs(self):
        user_profiles = super(UserProfileFilter, self).qs
        if not hasattr(self, '_users_info'):
            if u'courses' in self.data:
                courses = self.courses_qs.filter(id__in=self.data.getlist(u'courses'))
            else:
                courses = self.courses_qs

            if u'groups' in self.data:
                groups = self.groups_qs.filter(id__in=self.data.getlist(u'groups'))
            else:
                groups = self.groups_qs

            users_info = {}

            for issue in Issue.objects\
                    .filter(task__groups__in=groups,
                            task__course__in=courses,
                            task__is_hidden=False,
                            student__id__in=user_profiles.values_list('user__id', flat=True))\
                    .distinct()\
                    .select_related():
                users_info_key = '_'.join((str(issue.student.id), str(issue.task.course.id)))
                if users_info_key in users_info:
                    users_info[users_info_key]['sum_score'] += issue.mark
                else:
                    users_info[users_info_key] = {'user_profile': issue.student.get_profile(),
                                                  'course': issue.task.course,
                                                  'sum_score': issue.mark}

            if u'sum_score_0' in self.data or u'sum_score_1' in self.data:
                sum_score_start = float(self.data.get(u'sum_score_0')) if self.data.get(u'sum_score_0') else 0.0
                sum_score_end = float(self.data.get(u'sum_score_1')) if self.data.get(u'sum_score_1') else float('inf')

                for users_info_key in users_info.keys():
                    if not(sum_score_start <= users_info[users_info_key]['sum_score'] <= sum_score_end):
                        users_info.pop(users_info_key)

            self.users_info = users_info
            self._users_info = users_info

        return user_profiles

    def filter_course(self, qs, value):
        # if value and qs:
        #     return qs.filter(user__group__course__id__in=value).distinct()
        return qs

    def filter_group(self, qs, value):
        # if value and qs:
        #     return qs.filter(user__group__id__in=value).distinct()
        return qs

    def filter_sum_score(self, qs, value):
        return qs

    def set(self):
        self.courses_qs = Course.objects.filter(is_active=True)
        courses_choices = [(course.id, unicode(course)) for course in self.courses_qs]
        self.filters['courses'].field.choices = tuple(courses_choices)

        self.groups_qs = Group.objects.all()
        groups = [(group.id, unicode(group)) for group in self.groups_qs]
        self.filters['groups'].field.choices = tuple(groups)

        activity_choices = [(status.id, status.name) for status in UserStatus.objects.filter(type='activity')]
        self.filters['user_status'].field.choices = tuple(activity_choices)

        # print self.qs

        # education_form_choices = [(status.id, _(status.name)) for status in UserStatus.objects.filter(type='education_form')]
        # education_form_choices.insert(0, (u'', _(u'Любой')))
        # self.filters['user_status_education_form'].field.choices = tuple(education_form_choices)

    class Meta:
        model = UserProfile
        fields = ['courses', 'groups', 'user_status', 'sum_score']


# class AdvancedUserProfileFilter(django_filters.FilterSet):
#     # courses = django_filters.MultipleChoiceFilter(label=u'<strong>{0}</strong>'.format(_(u'Курс')), widget=forms.SelectMultiple)
#     # groups = django_filters.MultipleChoiceFilter(label=u'<strong>{0}</strong>'.format(_(u'Группа')), widget=forms.SelectMultiple)
#     user_status = django_filters.MultipleChoiceFilter(label=u'<strong>{0}</strong>'.format(_(u'Статус студента')), name='user_status', widget=forms.SelectMultiple)
#     # user_status_education_form = django_filters.ChoiceFilter(label=_(u'<strong>Форма обучения</strong>'), name='user_status')
#     sum_score__lt = django_filters.NumberFilter()
#     sum_score__gt = django_filters.NumberFilter()
#
#     @property
#     def qs(self):
#         parent = super(UserProfileFilter, self).qs
#         if self.is_bound and self.form.is_valid():
#
#
#         return parent
#
#     def set(self):
#         # courses = [(course.id, unicode(course)) for course in Course.objects.filter(is_active=True)]
#         # self.filters['courses'].field.choices = tuple(courses)
#         #
#         # groups = [(group.id, unicode(group)) for group in Group.objects.all()]
#         # self.filters['groups'].field.choices = tuple(courses)
#
#         activity_choices = [(status.id, status.name) for status in UserStatus.objects.filter(type='activity')]
#         self.filters['user_status'].field.choices = tuple(activity_choices)
#
#
#         # education_form_choices = [(status.id, _(status.name)) for status in UserStatus.objects.filter(type='education_form')]
#         # education_form_choices.insert(0, (u'', _(u'Любой')))
#         # self.filters['user_status_education_form'].field.choices = tuple(education_form_choices)
#
#
#
#     class Meta:
#         model = UserProfile
#         fields = ['user_status', 'sum_score__lt', 'sum_score__gt']


