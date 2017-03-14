# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext as _

from colorfield.fields import ColorField

import logging

logger = logging.getLogger('django.request')


class UserStatus(models.Model):
    COLOR_DEFAULT = '#818A91'

    STATUS_ACTIVE = 'active'
    STATUS_EXTRAMURAL = 'extramural'
    STATUS_FULLTIME = 'fulltime'
    STATUS_NOT_ACTIVE = 'not_active'
    STATUS_ACADEMIC = 'academic'

    USER_STATUSES = (
        (STATUS_ACTIVE, _(STATUS_ACTIVE)),
        (STATUS_EXTRAMURAL, _(STATUS_EXTRAMURAL)),
        (STATUS_FULLTIME, _(STATUS_FULLTIME)),
        (STATUS_NOT_ACTIVE, _(STATUS_NOT_ACTIVE)),
        (STATUS_ACADEMIC, _(STATUS_ACADEMIC))
    )

    TYPE_ACTIVITY = 'activity'
    TYPE_FILIAL = 'filial'
    TYPE_ADMISSION = 'admission'
    TYPE_EDUCATION_FORM = 'education_form'

    TYPE_STATUSES = (
        (TYPE_ACTIVITY, _(u'Статус студента')),
        (TYPE_FILIAL, _(u'Филлиал')),
        (TYPE_ADMISSION, _(u'Статус поступления')),
        # (TYPE_EDUCATION_FORM, _(u'Форма обучения')),
    )

    name = models.CharField(max_length=254, db_index=True, null=False, blank=False)
    type = models.CharField(max_length=191, db_index=False, null=True, blank=True, choices=TYPE_STATUSES)
    tag = models.CharField(max_length=254, db_index=False, null=True, blank=True, choices=USER_STATUSES)
    color = ColorField(default=COLOR_DEFAULT)

    def __unicode__(self):
        return u'{0}'.format(self.name)
