# coding: utf-8

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q

from issues.model_issue_status import IssueStatus


class DefaultForm(forms.Form):
    def __init__(self, field_name, request, issue, data=None, *args, **kwargs):
        self._field_name = field_name
        self._request = request
        self._issue = issue
        self._data = data

        if data:
            forms.Form.__init__(self, data, *args, **kwargs)
        else:
            forms.Form.__init__(self, request.POST, request.FILES, *args, **kwargs)


def user_id2user(user_id):
    return User.objects.get(id=user_id)


def get_users_choise(issue, field=None):
    users = []
    qs_filter = Q()
    if field == 'responsible':
        qs_filter = Q(id=issue.responsible_id)
    elif field == 'followers':
        qs_filter = Q(id__in=issue.followers.all().values_list("id", flat=True))

    for user in User.objects.filter(Q(is_staff=True) | Q(course_teachers_set=issue.task.course) | qs_filter).distinct():
        users.append((user.id, user.get_full_name()))

    return users


def get_responsible_form(field_name, request, issue, data=None, *args, **kwargs):
    class _form(DefaultForm):
        responsible_name = forms.TypedChoiceField(get_users_choise(issue, 'responsible'), coerce=user_id2user, label='',
                                                  required=False)

    return _form(field_name, request, issue, data, *args, **kwargs)


def get_followers_form(field_name, request, issue, data=None, *args, **kwargs):
    class _form(DefaultForm):
        followers_names = forms.MultipleChoiceField(get_users_choise(issue, 'followers'), required=False,
                                                    label='')  # we dont need coerce function here
        # because add user id to m2m field is ok.

    return _form(field_name, request, issue, data, *args, **kwargs)


def get_status_choice(issue, lang):
    statuses = []
    for status in issue.task.course.issue_status_system.statuses.all().exclude(tag=IssueStatus.STATUS_SEMINAR):
        statuses.append((status.id, status.get_name(lang)))
    return statuses


def status_id2status(status_id):
    return IssueStatus.objects.get(id=status_id)


def get_status_form(field_name, request, issue, data=None, *args, **kwargs):
    class _form(DefaultForm):
        lang = request.user.profile.language
        status = forms.TypedChoiceField(get_status_choice(issue, lang),
                                        coerce=status_id2status, label='', required=False)

    return _form(field_name, request, issue, data, *args, **kwargs)


class MultiFileInput(forms.FileInput):
    def render(self, name, value, attrs=None):
        attrs['multiple'] = 'multiple'
        return super(MultiFileInput, self).render(name, None, attrs=attrs)

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        else:
            return [files.get(name)]


class MultiFileField(forms.FileField):
    widget = MultiFileInput
    default_error_messages = {
        'min_num': u'Ensure at least %(min_num)s files are uploaded (received %(num_files)s).',
        'max_num': u'Ensure at most %(max_num)s files are uploaded (received %(num_files)s).',
        'file_size': u'File: %(uploaded_file_name)s, exceeded maximum upload size.'
    }

    def __init__(self, *args, **kwargs):
        self.min_num = kwargs.pop('min_num', 0)
        self.max_num = kwargs.pop('max_num', None)
        self.maximum_file_size = kwargs.pop('maximum_file_size', None)
        super(MultiFileField, self).__init__(*args, **kwargs)

    def to_python(self, data):
        ret = []
        for item in data:
            ret.append(super(MultiFileField, self).to_python(item))
        return ret

    def validate(self, data):
        while None in data:  # Got data == [None] when there is no files.
            data.remove(None)

        super(MultiFileField, self).validate(data)
        num_files = len(data)
        if len(data) and not data[0]:
            num_files = 0
        if num_files < self.min_num:
            raise ValidationError(self.error_messages['min_num'] % {'min_num': self.min_num, 'num_files': num_files})
            return
        elif self.max_num and num_files > self.max_num:
            raise ValidationError(self.error_messages['max_num'] % {'max_num': self.max_num, 'num_files': num_files})
        for uploaded_file in data:
            if uploaded_file.size > self.maximum_file_size:
                raise ValidationError(self.error_messages['file_size'] % {'uploaded_file_name': uploaded_file.name})


class CommentForm(DefaultForm):
    textarea_attrs = {
        'placeholder': 'Comment...',
        'class': 'span12',
        'rows': '4',
    }

    comment = forms.CharField(max_length=2500,
                              widget=forms.Textarea(attrs=textarea_attrs),
                              label='',
                              required=False)

    files = MultiFileField(label='', required=False, max_num=10, min_num=0, maximum_file_size=settings.MAX_FILE_SIZE)


class IntForm(DefaultForm):
    value = forms.IntegerField(label='')


class MarkForm(DefaultForm):
    float_field_attrs = {
        'placeholder': _(u'format14')
    }
    mark = forms.FloatField(label='',
                            widget=forms.TextInput(attrs=float_field_attrs),
                            required=False)


# class StatusForm(DefaultForm):
#
#     STATUS_NEW = 'new'
#     STATUS_REWORK = 'rework'
#     STATUS_VERIFICATION = 'verification'
#     STATUS_ACCEPTED = 'accepted'
#
#     ISSUE_STATUSES = (
#         # (STATUS_NEW, _(u'Новый')),
#         (STATUS_REWORK, _(u'На доработке')),
#         (STATUS_VERIFICATION, _(u'На проверке')),
#         (STATUS_ACCEPTED, _(u'Зачтено')),
#     )
#
#     status = forms.ChoiceField(choices=ISSUE_STATUSES, label="", required=False)


class FileForm(DefaultForm):
    file = forms.FileField(label='')
