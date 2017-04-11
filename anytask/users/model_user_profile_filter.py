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
    user_status_activity = CustomMethodFilter(label=_(u'status_studenta'),
                                              action='empty_filter',
                                              widget=forms.SelectMultiple,
                                              field_class=forms.MultipleChoiceField)
    user_status_filial = CustomMethodFilter(label=_(u'filial'),
                                            action='empty_filter',
                                            widget=forms.SelectMultiple,
                                            field_class=forms.MultipleChoiceField)
    user_status_admission = CustomMethodFilter(label=_(u'status_postupleniya'),
                                               action='empty_filter',
                                               widget=forms.SelectMultiple,
                                               field_class=forms.MultipleChoiceField)

    STATUS_SQL_JOIN = 'LEFT OUTER JOIN users_userprofile_user_status {0} ' \
                      'ON (users_userprofile.id = {0}.userprofile_id)'
    STATUS_SQL_PREFIX = 'UUUS'
    STATUS_SQL_EXTRA = '''
        users_userprofile.id IN (
          SELECT DISTINCT
            users_userprofile.id
          FROM users_userprofile
          {0}
          WHERE {1}
        )
    '''

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

    def get_extra_sql_statuses(self):
        status_join = []
        status_where = []
        status_type_counter = 0
        for filter_name in [u'user_status_activity', u'user_status_filial', u'user_status_admission']:
            if filter_name in self.data:
                status_type_counter += 1
                table_name = self.STATUS_SQL_PREFIX + str(status_type_counter)

                status_join.append(self.STATUS_SQL_JOIN.format(table_name))
                status_where.append(
                    '({0}.userstatus_id = {1})'
                        .format(table_name,
                                ' OR {0}.userstatus_id = '.join(self.data.getlist(filter_name)).format(table_name))
                )

        if status_type_counter:
            return self.STATUS_SQL_EXTRA.format(' '.join(status_join), ' AND '.join(status_where))
        return ''

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

                profiles_info = qs.filter(**qs_filter).values(
                    'id',
                    'user__id',
                    'user__username',
                    'user__email',
                    'user__last_name',
                    'user__first_name',
                    'user_status__id',
                    'user_status__name',
                    'user_status__color'
                )

                extra_sql = self.get_extra_sql_statuses()
                if extra_sql:
                    profiles_info = profiles_info.extra(where=[extra_sql])

                users_info = {}
                for info in profiles_info:
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
                self.users_info = users_info
        return self._qs

    class Meta:
        model = UserProfile
        fields = ['courses', 'groups', 'user_status_filial', 'user_status_activity', 'user_status_admission']
