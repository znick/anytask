# -*- coding: utf-8 -*-

import datetime
import hashlib
import json
import logging
import random
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
from django.template.loader import render_to_string

from mail.common import send_mass_mail_html
from registration.models import RegistrationManager

logger = logging.getLogger('django.request')

SHA1_RE = re.compile('^[a-f0-9]{40}$')


def send_mail_admin(subject, message=None, request=None):
    if not message:
        message = ''

    if request:
        message += '\n\nMETA\n%s' % request.META
        message += '\n\nmethod\n%s' % request.method
        if request.method == 'GET':
            message += '\n\nGET\n%s' % request.GET
        elif request.method == 'POST':
            message += '\n\nPOST\n%s' % request.POST

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, settings.DEFAULT_FROM_EMAIL)


class AdmissionRegistrationProfileManager(RegistrationManager):
    def create_or_update_user(self, username, email, password, uid=None, send_email=True, request=None):
        user_by_username = User.objects.filter(username=username)
        user_by_email = User.objects.filter(email=email)

        if uid:
            user_by_uid = User.objects.filter(Q(profile__ya_passport_uid=uid) | Q(profile__ya_contest_uid=uid))
        else:
            user_by_uid = User.objects.none()
        user = registration_profile = None

        if not (user_by_username | user_by_email | user_by_uid):
            user, registration_profile = self.create_inactive_user(username, email, password, send_email)
            logger.info("Admission: User %s was created", user.username)
        elif user_by_username and not (user_by_email | user_by_uid):
            new_username = self.generate_username()
            user, registration_profile = self.create_inactive_user(new_username, email, password, send_email)
            logger.info("Admission: User with email %s was created with generated login %s", user.email, user.username)
        else:
            self.send_mail_update_user(email)
            logger.warning("Admission: User with email %s and uid %s already created", email, uid)

        # elif len(user_by_email | user_by_uid) == 1:
        #     user, registration_profile = self.update_user((user_by_email | user_by_uid)[0], send_email)
        #     logger.info("Admission: User %s was updated", user.username)
        # else:
        #     send_mail_admin(u'Ошибка поступления', message='User not created (already registered)', request=request)
        #     logger.error("Admission: User not created (already registered) %s %s %s", username, email, uid)

        return user, registration_profile

    def create_inactive_user(self, username, email, password, send_email=True):
        new_user = User.objects.create_user(username, email, password)
        new_user.is_active = False
        new_user.save()

        registration_profile = self.create_profile(new_user)

        if send_email:
            registration_profile.send_activation_email(Site.objects.get_current())

        return new_user, registration_profile

    def create_profile(self, user):
        """
        Create a ``RegistrationProfile`` for a given
        ``User``, and return the ``RegistrationProfile``.

        The activation key for the ``RegistrationProfile`` will be a
        SHA1 hash, generated from a combination of the ``User``'s
        username and a random salt.

        """
        salt = hashlib.sha1(str(random.random()).encode('utf8')).hexdigest()[:5]
        username = user.username
        if isinstance(username, str):
            username = username
        activation_key = hashlib.sha1((salt + username).encode('utf8')).hexdigest()
        return self.create(user=user,
                           activation_key=activation_key)

    def send_mail_update_user(self, email):

        subject = render_to_string('email_update_subject.txt')
        subject = ''.join(subject.splitlines())

        context = {}

        plain_text = render_to_string('email_update.txt', context)
        html = render_to_string('email_update.html', context)

        send_mass_mail_html([(subject, plain_text, html, settings.DEFAULT_FROM_EMAIL, [email])])

    def update_user(self, user, send_email=False):
        registration_profile = self.create_profile(user)
        registration_profile.is_updating = True
        registration_profile.save()

        if send_email:
            registration_profile.send_activation_email(Site.objects.get_current())

        return user, registration_profile

    @staticmethod
    def generate_username():
        while True:
            username = hashlib.sha1(str(random.random())).hexdigest()[:7]
            if not User.objects.filter(username=username).count():
                break
        return username

    def activate_user(self, activation_key):
        if SHA1_RE.search(activation_key):
            has_profile = True
            try:
                profile = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                has_profile = False
            if has_profile and not profile.activation_key_expired():
                user = profile.user
                user.is_active = True
                user.save()
                profile.activation_key = self.model.ACTIVATED
                profile.old_activation_key = activation_key
                profile.save()
                return user, profile.user_info if profile.is_updating else None
            else:
                return self.get_activated_user(activation_key), None
        return False, None

    def get_activated_user(self, activation_key):
        try:
            profile = self.get(old_activation_key=activation_key)
        except self.model.DoesNotExist:
            return False
        return profile.user

    def decline_user(self, activation_key):
        if SHA1_RE.search(activation_key):
            try:
                profile = self.get(activation_key=activation_key)
                profile.activation_key = self.model.DECLINED
                profile.save()
            except self.model.DoesNotExist:
                return None
            return profile
        return None


class AdmissionRegistrationProfile(models.Model):
    user = models.ForeignKey(User, unique=False, null=False, blank=False)
    activation_key = models.CharField(max_length=40, null=True, blank=True)
    old_activation_key = models.CharField(max_length=40, null=True, blank=True)
    is_updating = models.BooleanField(default=False)
    user_info = models.TextField(null=True, blank=True)

    ACTIVATED = u"ALREADY_ACTIVATED"
    DECLINED = u"DECLINED"

    objects = AdmissionRegistrationProfileManager()

    def activation_key_expired(self):
        expiration_date = datetime.datetime.strptime(settings.ADMISSION_DATE_END, "%d.%m.%y %H:%M")
        return expiration_date <= datetime.datetime.now()

    def activation_key_activated(self):
        return self.activation_key == self.ACTIVATED

    def send_activation_email(self, site=None):
        if not site:
            site = Site.objects.get_current()

        subject = render_to_string('email_activate_subject.txt')
        subject = ''.join(subject.splitlines())

        context = {
            'user': self.user,
            'user_info': json.loads(self.user_info),
            'domain': str(site),
            'activation_key': self.activation_key,
            'is_updating': self.is_updating
        }

        plain_text = render_to_string('email_activate.txt', context)
        html = render_to_string('email_activate.html', context)

        send_mass_mail_html([(subject, plain_text, html, settings.DEFAULT_FROM_EMAIL, [self.user.email])])
