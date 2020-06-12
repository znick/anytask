# coding: utf-8

import re

from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.sites.requests import RequestSite
from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _
from django.utils.translation import get_language_from_request
from django import forms
from django.contrib.auth.tokens import default_token_generator
from users.models import UserProfile
from django.template.loader import render_to_string
from django.utils.http import int_to_base36
from django.utils import translation

from registration import signals
from registration.forms import RegistrationForm, RegistrationFormUniqueEmail
from registration.models import RegistrationProfile

from mail.common import send_mass_mail_html

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML

attrs_dict = { 'class': 'required' }


class AnytaskLoginForm(AuthenticationForm):
    username = forms.CharField(label=_("Username"), max_length=75)

    def __init__(self, *args, **kwargs):
        AuthenticationForm.__init__(self, *args, **kwargs)
        self.error_messages['invalid_login'] = "Пожалуйста, введите верные имя пользователя / адрес электронной почты и пароль."
        self.fields['username'].label = _(u"Логин / E-mail")

        self.helper = FormHelper(self)
        self.helper.form_action = '/accounts/login/'
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-8'
        self.helper.layout.append(HTML(u"""<div class="form-group row" style="margin-bottom: 16px;margin-top: -16px;">
                                             <div class="col-md-offset-4 col-md-8">
                                               <a href="{% url "auth_password_reset" %}"><small class="text-muted">""" + _(u'Забыли пароль?') + """</small></a>
                                             </div>
                                           </div>
                                           <div class="form-group row">
                                             <div class="col-md-offset-4 col-md-8">
                                               <button type="submit" class="btn btn-secondary">""" + _(u'Войти') + """</button>
                                               <input type="hidden" name="next" value="{{ next }}" />
                                             </div>
                                           </div>"""))

    def clean_username(self):
        username = self.cleaned_data.get('username', '')

        try:
            user = User.objects.get(username__iexact=username)
            return user.username
        except User.DoesNotExist:
            pass

        try:
            user = User.objects.get(email__iexact=username)
            return user.username
        except User.DoesNotExist:
            pass

        return username

class AnytaskPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        PasswordResetForm.__init__(self, *args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.label_class = 'col-md-5'
        self.helper.field_class = 'col-md-7'
        self.helper.layout.append(HTML(u"""<div class="form-group row">
                                             <div class="col-md-offset-5 col-md-7">
                                               <button type="submit" class="btn btn-secondary">""" + _(u'Сбросить') + """</button>
                                             </div>
                                           </div>"""))

    def save(self, *args, **kwargs):
        kwargs['email_template_name'] = 'registration/password_reset_email.txt'
        kwargs['html_email_template_name'] = 'registration/password_reset_email.html'
        PasswordResetForm.save(self, *args, **kwargs)


class AnytaskSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        SetPasswordForm.__init__(self, *args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-8'
        self.helper.layout.append(HTML(u"""<div class="form-group row">
                                             <div class="col-md-offset-4 col-md-8">
                                               <button type="submit" class="btn btn-secondary">""" + _(u'Применить') + """</button>
                                             </div>
                                           </div>"""))


class AnytaskPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        PasswordChangeForm.__init__(self, *args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.label_class = 'col-md-5'
        self.helper.field_class = 'col-md-7'
        self.helper.layout.append(HTML(u"""<div class="form-group row">
                                             <div class="col-md-offset-5 col-md-7">
                                               <button type="submit" class="btn btn-secondary">""" + _(u'Изменить') + """</button>
                                             </div>
                                           </div>"""))


class RegistrationFormWithNames(RegistrationForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs=attrs_dict))
    last_name = forms.CharField(widget=forms.TextInput(attrs=attrs_dict))
    show_email = forms.BooleanField(required=False, initial=True)
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_("Password (again)"))
    #invite = forms.CharField(widget=forms.TextInput(attrs=attrs_dict), label="Инвайт")

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = _(u"Логин")
        self.fields['first_name'].label = _(u"Имя")
        self.fields['last_name'].label = _(u"Фамилия")
        self.fields['show_email'].label = _(u"Показывать мой e-mail всем пользователям")

        self.fields.keyOrder = [
            'username',
            'first_name',
            'last_name',
            'email',
            'show_email',
            'password1',
            'password2',
            #'invite',
        ]


class RegistrationFormWithNamesUniqEmail(RegistrationFormWithNames, RegistrationFormUniqueEmail):
    pass

class BootStrapRegistrationFormWithNames(RegistrationFormWithNamesUniqEmail):
    def __init__(self, *args, **kwargs):
        RegistrationFormWithNamesUniqEmail.__init__(self, *args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.label_class = 'col-md-4'
        self.helper.field_class = 'col-md-8'
        self.helper.layout.append(HTML(u"""<div class="form-group row">
                                             <div class="col-md-offset-4 col-md-8">
                                               <button type="submit" class="btn btn-secondary">""" + _(u'Зарегистрироваться') + """</button>
                                             </div>
                                           </div>"""))



class DefaultBackend(object):
    """
    A registration backend which follows a simple workflow:

    1. User signs up, inactive account is created.

    2. Email is sent to user with activation link.

    3. User clicks activation link, account is now active.

    Using this backend requires that

    * ``registration`` be listed in the ``INSTALLED_APPS`` setting
      (since this backend makes use of models defined in this
      application).

    * The setting ``ACCOUNT_ACTIVATION_DAYS`` be supplied, specifying
      (as an integer) the number of days from registration during
      which a user may activate their account (after that period
      expires, activation will be disallowed).

    * The creation of the templates
      ``registration/activation_email_subject.txt`` and
      ``registration/activation_email.txt``, which will be used for
      the activation email. See the notes for this backends
      ``register`` method for details regarding these templates.

    Additionally, registration can be temporarily closed by adding the
    setting ``REGISTRATION_OPEN`` and setting it to
    ``False``. Omitting this setting, or setting it to ``True``, will
    be interpreted as meaning that registration is currently open and
    permitted.

    Internally, this is accomplished via storing an activation key in
    an instance of ``registration.models.RegistrationProfile``. See
    that model and its custom manager for full documentation of its
    fields and supported operations.

    """
    def register(self, request, **kwargs):
        """
        Given a username, email address and password, register a new
        user account, which will initially be inactive.

        Along with the new ``User`` object, a new
        ``registration.models.RegistrationProfile`` will be created,
        tied to that ``User``, containing the activation key which
        will be used for this account.

        An email will be sent to the supplied email address; this
        email should contain an activation link. The email will be
        rendered using two templates. See the documentation for
        ``RegistrationProfile.send_activation_email()`` for
        information about these templates and the contexts provided to
        them.

        After the ``User`` and ``RegistrationProfile`` are created and
        the activation email is sent, the signal
        ``registration.signals.user_registered`` will be sent, with
        the new ``User`` as the keyword argument ``user`` and the
        class of this backend as the sender.

        """
        username, email, password = kwargs['username'], kwargs['email'], kwargs['password1']
        first_name, last_name, show_email = kwargs['first_name'], kwargs['last_name'], kwargs['show_email']
        #invite = get_object_or_404(Invite, key=invite_key)

        if Site._meta.installed:
            site = Site.objects.get_current()
        else:
            site = RequestSite(request)
        new_user = RegistrationProfile.objects.create_inactive_user(username, email,
                                                                    password, site)

        new_user.first_name = first_name
        new_user.last_name = last_name
        new_user.save()

        new_user_profile = UserProfile.objects.get(user=new_user)
        new_user_profile.show_email = show_email
        new_user_profile.language = get_language_from_request(request)
        new_user_profile.save()

        #if invite.group:
        #    invite.group.students.add(new_user)
        #invite.invited_user = new_user
        #invite.save()

        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=request)
        return new_user

    def activate(self, request, activation_key):
        """
        Given an an activation key, look up and activate the user
        account corresponding to that key (if possible).

        After successful activation, the signal
        ``registration.signals.user_activated`` will be sent, with the
        newly activated ``User`` as the keyword argument ``user`` and
        the class of this backend as the sender.

        """
        activated = RegistrationProfile.objects.activate_user(activation_key)
        if activated:
            signals.user_activated.send(sender=self.__class__,
                                        user=activated,
                                        request=request)
        return activated

    def registration_allowed(self, request):
        """
        Indicate whether account registration is currently permitted,
        based on the value of the setting ``REGISTRATION_OPEN``. This
        is determined as follows:

        * If ``REGISTRATION_OPEN`` is not specified in settings, or is
          set to ``True``, registration is permitted.

        * If ``REGISTRATION_OPEN`` is both specified and set to
          ``False``, registration is not permitted.

        """
        return getattr(settings, 'REGISTRATION_OPEN', True)

    def get_form_class(self, request):
        """
        Return the default form class used for user registration.

        """
        return BootStrapRegistrationFormWithNames

    def post_registration_redirect(self, request, user):
        """
        Return the name of the URL to redirect to after successful
        user registration.

        """
        return ('registration_complete', (), {})

    def post_activation_redirect(self, request, user):
        """
        Return the name of the URL to redirect to after successful
        account activation.

        """
        return ('registration_activation_complete', (), {})
