# coding: utf-8
from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _
from invites.models import Invite
from django.utils import timezone

import datetime

attrs_dict = {'class': 'required'}


class InviteActivationForm(forms.Form):
    invite = forms.CharField(widget=forms.TextInput(attrs=attrs_dict), label="")

    def clean_invite(self):
        """
        Validate that the invite is not already
        in use and exists.
        """

        try:
            invite = Invite.objects.get(key=self.cleaned_data['invite'])
        except:  # noqa
            raise forms.ValidationError(_(u"invajta_ne_sushestvuet"))

        if invite.added_time + datetime.timedelta(days=settings.INVITE_EXPIRED_DAYS) < timezone.now():
            raise forms.ValidationError(_(u"srok_dejstvija_invajta_istek"))
        else:
            return self.cleaned_data['invite']
