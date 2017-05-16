# coding: utf-8

from django.db import models
from django.utils.translation import ugettext_lazy as _

from colorfield.fields import ColorField


class IssueStatus(models.Model):
    COLOR_DEFAULT = '#818A91'

    STATUS_NEW = 'new'
    STATUS_AUTO_VERIFICATION = 'auto_verification'
    STATUS_NEED_INFO = 'need_info'
    HIDDEN_STATUSES = {STATUS_NEW: 1,
                       STATUS_AUTO_VERIFICATION: 2,
                       STATUS_NEED_INFO: 6}

    STATUS_REWORK = 'rework'
    STATUS_VERIFICATION = 'verification'
    STATUS_ACCEPTED = 'accepted'
    STATUS_SEMINAR = 'seminar'
    STATUS_ACCEPTED_AFTER_DEADLINE = 'accepted_after_deadline'

    RU_NAME_KEY = {
        u'Новый': _('novyj'),
        u'На доработке':  _('na_dorabotke'),
        u'На проверке': _('na_proverke'),
        u'Зачтено': _('zachteno'),
        u'Зачтено после дедлайна': _('zachteno_posle_dedlajna'),
        u'На автоматической проверке': _('na_avtomaticheskoj_proverke'),
        u'Требуется информация': _('trebuetsja_informacija')
    }

    ISSUE_STATUSES = (
        (STATUS_REWORK, _(STATUS_REWORK)),
        (STATUS_VERIFICATION, _(STATUS_VERIFICATION)),
        (STATUS_ACCEPTED, _(STATUS_ACCEPTED)),
        (STATUS_SEMINAR, _(STATUS_SEMINAR)),
        (STATUS_ACCEPTED_AFTER_DEADLINE, _(STATUS_ACCEPTED_AFTER_DEADLINE))
    )

    name = models.CharField(max_length=191, db_index=True, null=False, blank=False)
    tag = models.CharField(max_length=191, db_index=False, null=True, blank=True, choices=ISSUE_STATUSES)
    color = ColorField(default=COLOR_DEFAULT)

    hidden = models.BooleanField(default=False)

    def get_name(self):
        name = u'{0}'.format(self.name)
        if name in self.RU_NAME_KEY:
            name = unicode(self.RU_NAME_KEY[name])
        return name

    def __unicode__(self):
        return u'{0}'.format(self.get_name())


class IssueStatusSystem(models.Model):
    name = models.CharField(max_length=191, db_index=False, null=False, blank=False)
    statuses = models.ManyToManyField(IssueStatus, null=True, blank=True)

    def __unicode__(self):
        return u'{0}'.format(self.name)

    def has_accepted_after_deadline(self):
        return self.statuses.filter(tag='accepted_after_deadline').exists()

    def get_accepted_statuses(self):
        return self.statuses.filter(tag__in=['accepted', 'accepted_after_deadline'])
