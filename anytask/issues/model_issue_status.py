# coding: utf-8

from django.db import models
from django.utils.translation import ugettext_lazy as _
from common.locale_funcs import validate_json, get_value_from_json

from colorfield.fields import ColorField


class IssueStatus(models.Model):
    COLOR_DEFAULT = '#818A91'
    NAME_DEFAULT = _(u"novyj")

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

    ISSUE_STATUSES = (
        (STATUS_REWORK, _(STATUS_REWORK)),
        (STATUS_VERIFICATION, _(STATUS_VERIFICATION)),
        (STATUS_ACCEPTED, _(STATUS_ACCEPTED)),
        (STATUS_SEMINAR, _(STATUS_SEMINAR)),
        (STATUS_ACCEPTED_AFTER_DEADLINE, _(STATUS_ACCEPTED_AFTER_DEADLINE))
    )

    name = models.CharField(max_length=191, db_index=True, null=False, blank=False,
                            help_text=u'Format is {"ru": "Cеминар", "en": "Seminar", etc.} or {"ru": "Cеминар"}',
                            validators=[validate_json])
    tag = models.CharField(max_length=191, db_index=False, null=True, blank=True, choices=ISSUE_STATUSES)
    color = ColorField(default=COLOR_DEFAULT)

    hidden = models.BooleanField(default=False)

    def get_name(self, lang='ru'):
        return get_value_from_json(self.name, lang)

    def __unicode__(self):
        return u'{0}'.format(self.get_name())

    class Meta:
        verbose_name = _('issue status')
        verbose_name_plural = _('issue statuses')


class IssueStatusSystem(models.Model):
    name = models.CharField(max_length=191, db_index=False, null=False, blank=False)
    statuses = models.ManyToManyField(IssueStatus, blank=True)

    def __unicode__(self):
        return u'{0}'.format(self.name)

    def has_accepted_after_deadline(self):
        return self.statuses.filter(tag='accepted_after_deadline').exists()

    def get_accepted_statuses(self):
        return self.statuses.filter(tag__in=['accepted', 'accepted_after_deadline'])
