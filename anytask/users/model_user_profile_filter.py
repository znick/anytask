# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django import forms

from collections import defaultdict

from groups.models import Group
from courses.models import Course
from users.models import UserProfile
from users.model_user_status import UserStatus

import django_filters
import logging

logger = logging.getLogger('django.request')


class CustomMethodFilter(django_filters.MethodFilter):
    def __init__(self, *args, **kwargs):
        self.field_class = kwargs.pop('field_class', forms.Field)

        super(CustomMethodFilter, self).__init__(*args, **kwargs)


class UserProfileFilter(django_filters.FilterSet):
    courses = CustomMethodFilter(label=_(u'kurs'),
                                 action='empty_filter',
                                 widget=forms.SelectMultiple,
                                 field_class=forms.MultipleChoiceField)
    groups = CustomMethodFilter(label=_(u'gruppa'),
                                action='empty_filter',
                                widget=forms.SelectMultiple,
                                field_class=forms.MultipleChoiceField)
    user_status_activity = django_filters.MultipleChoiceFilter(
        label=_(u'status_studenta'),
        name='user_status',
        widget=forms.SelectMultiple)
    user_status_filial = django_filters.MultipleChoiceFilter(
        label=_(u'filial'),
        name='user_status',
        widget=forms.SelectMultiple)
    user_status_admission = django_filters.MultipleChoiceFilter(
        label=_(u'status_postupleniya'),
        name='user_status',
        widget=forms.SelectMultiple)

    @property
    def qs(self):
        if not hasattr(self, '_qs'):
            qs = super(UserProfileFilter, self).qs
            if not hasattr(self, '_users_info'):
                qs_filter = {}

                if u'courses' in self.data:
                    qs_filter['user__group__course__id__in'] = self.data.getlist(u'courses')
                if u'groups' in self.data:
                    qs_filter['user__group__id__in'] = self.data.getlist(u'groups')

                users_info = {}
                for info in qs.filter(**qs_filter).values(
                        'id',
                        'user__id',
                        'user__username',
                        'user__email',
                        'user__last_name',
                        'user__first_name',
                        'user_status__id',
                        'user_status__name',
                        'user_status__color',
                        # 'user__group__course__id',
                        # 'user__group__course__name',
                        # 'user__group__course__is_active'
                ):
                    if info['user__id'] not in users_info:
                        users_info[info['user__id']] = defaultdict(dict)
                        users_info[info['user__id']]['id_profile'] = info['id']
                        users_info[info['user__id']]['username'] = info['user__username']
                        users_info[info['user__id']]['email'] = info['user__email']
                        users_info[info['user__id']]['last_name'] = info['user__last_name']
                        users_info[info['user__id']]['first_name'] = info['user__first_name']
                    if info['user_status__id']:
                        users_info[info['user__id']]['statuses'][info['user_status__id']] = {
                            'name': info['user_status__name'],
                            'color': info['user_status__color'],
                        }
                        # users_info[info['user__id']]['courses'][info['user__group__course__id']] = {
                        #     'name': info['user__group__course__name']
                        # }
                self.users_info = users_info
        return self._qs

    def empty_filter(self, qs, value):
        return qs

    # def filter_course(self, qs, value):
    #     if not hasattr(self, '_qs'):
    #         if value and qs:
    #             return qs.filter(user__group__course__id__in=value).distinct()
    #     return qs
    #
    # def filter_group(self, qs, value):
    #     if not hasattr(self, '_qs'):
    #         if value and qs:
    #             return qs.filter(user__group__id__in=value).distinct()
    #     return qs

    def set(self):
        for field in self.filters:
            self.filters[field].field.label = u'<strong>{0}</strong>'.format(self.filters[field].field.label)

        self.courses_qs = Course.objects.filter(is_active=True)
        courses_choices = [(course.id, course.name) for course in self.courses_qs]
        self.filters['courses'].field.choices = tuple(courses_choices)

        self.groups_qs = Group.objects.all()
        groups = [(group.id, group.name) for group in self.groups_qs]
        self.filters['groups'].field.choices = tuple(groups)

        activity_choices = []
        filial_choices = []
        admission_choices = []
        for status in UserStatus.objects.exclude(type__isnull=True):
            if status.type == 'activity':
                activity_choices.append((status.id, status.name))
            elif status.type == 'filial':
                filial_choices.append((status.id, status.name))
            elif status.type == 'admission':
                admission_choices.append((status.id, status.name))

        self.filters['user_status_activity'].field.choices = tuple(activity_choices)
        self.filters['user_status_filial'].field.choices = tuple(filial_choices)
        self.filters['user_status_admission'].field.choices = tuple(admission_choices)

    class Meta:
        model = UserProfile
        fields = ['courses', 'groups', 'user_status_filial', 'user_status_activity', 'user_status_admission']
