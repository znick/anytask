# coding: utf-8
from django import forms
from django.conf import settings
from invites.models import Invite

import datetime

attrs_dict = { 'class': 'required' }

class InviteActivationForm(forms.Form):
    invite = forms.CharField(widget=forms.TextInput(attrs=attrs_dict), label="Инвайт в группу:")

    def clean_invite(self):
        """
        Validate that the invite is not already
        in use and exists.
        """

        try:
            invite = Invite.objects.get(key=self.cleaned_data['invite'])
        except:
            raise forms.ValidationError("Такого инвайта не существует.")

        if invite.added_time + datetime.timedelta(days=settings.INVITE_EXPIRED_DAYS) < datetime.datetime.now():
            raise forms.ValidationError("Срок действия инвайта истек.")
        else:
            return self.cleaned_data['invite']