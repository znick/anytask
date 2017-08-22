# coding: utf-8
import json

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from colorfield.fields import ColorField


def validate_json(value):
    try:
        json_name = json.loads(value)
        if 'ru' not in json_name:
            raise KeyError
    except ValueError:
        raise ValidationError(u'%s is not a json string' % value)
    except KeyError:
        raise ValidationError(u'%s does not contains required "ru" key' % value)


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
        try:
            json_name = json.loads(self.name)
            if lang in json_name:
                name = json_name[lang]
            else:
                name = json_name['ru']
        except ValueError:
            name = self.name
        name = u'{0}'.format(name)
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
