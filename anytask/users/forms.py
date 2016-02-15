from django import forms
from django.conf import settings
from invites.models import Invites

import datetime

class InviteActivationForm(forms.Form):
    invite = forms.CharField(widget=forms.TextInput(attrs=attrs_dict), label="Инвайт в группу:")

    def clean_invite(self):
        """
        Validate that the invite is not already
        in use and exists.
        """

        invite = self.cleaned_data['invite']
        if invite.added_time + datetime.timedelta(days=settings.INVITE_EXPIRED_DAYS) > datetime.date.today():
            raise forms.ValidationError("Срок действия инвайта истек.")
        else:
            return self.cleaned_data['invite']