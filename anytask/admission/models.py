# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.contrib.sites.models import Site
from registration.models import RegistrationProfile, RegistrationManager
from django.template.loader import render_to_string
from django.db.models import Q
from django.core.mail import send_mail

from django.contrib.auth.models import User
# from users.models import UserProfile

import datetime
import hashlib
import random
import logging
import re


logger = logging.getLogger('django.request')

SHA1_RE = re.compile('^[a-f0-9]{40}$')

def send_mail_admin(subject, message=None, request=None):
    if not message:
        message = ''

    if request:
        message += '\n\nMETA\n%s' % request.META
        if request.method == 'GET':
            message += '\n\nGET\n%s' % request.GET
        elif request.method == 'POST':
            message += '\n\nPOST\n%s' % request.POST

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, settings.DEFAULT_FROM_EMAIL)


class AdmissionRegistrationProfileManager(RegistrationManager):
    site = Site.objects.get_current()

    def create_or_update_user(self, username, email, password, uid=None, send_email=True, request=None):
        user_by_username = User.objects.filter(username=username)
        user_by_email = User.objects.filter(email=email)
        # if uid:
        #     user_by_uid = [u_p.user for u_p in
        #                    UserProfile.objects.filter(Q(ya_passport_uid=uid) | Q(ya_contest_uid=uid))]
        # else:
        user_by_uid = User.objects.none()
        users = user_by_username | user_by_email | user_by_uid

        if not users:
            return self.create_inactive_user(username, email, password, send_email), True
        elif user_by_username and not (user_by_email | user_by_uid):
            new_username = self.generate_username()
            user = self.create_inactive_user(new_username, email, password, send_email)
            logger.info("Admission: User with email %s was created with generated login %s", user.email, user.username)
            return user, True
        elif len(users) == 1:
            return self.update_user(users[0]), False
        else:
            logger.error("Admission: User not created ", username, email, uid)
            send_mail_admin(u'Ошибка поступления', request=request)
            return None, False

    def create_inactive_user(self, username, email, password, send_email=True):
        return super(AdmissionRegistrationProfileManager, self).create_inactive_user(username, email, password,
                                                                                     self.site, send_email)

    def update_user(self, user):
        logger.info("Admission: User %s was updated", user.username)
        # TODO: email user about update
        return user

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
                return user
            else:
                return self.get_activated_user(activation_key)
        return False

    def get_activated_user(self, activation_key):
        try:
            profile = self.get(old_activation_key=activation_key)
        except self.model.DoesNotExist:
            return False
        return profile.user


class AdmissionRegistrationProfile(RegistrationProfile):
    objects = AdmissionRegistrationProfileManager()
    old_activation_key = ''

    def activation_key_expired(self):
        expiration_date = datetime.datetime.strptime(settings.ADMISSION_DATE_END, "%d.%m.%y %H:%M")
        return expiration_date <= datetime.datetime.now()

    def activation_key_activated(self):
        return self.activation_key == self.ACTIVATED

    def send_activation_email(self, site):
        subject = render_to_string('email_activate_subject.txt')
        subject = ''.join(subject.splitlines())

        context = {
            'user': self.user,
            'domain': 'http://' + str(site),
            'activation_key': self.activation_key
        }

        plain_text = '...'
        html = render_to_string('email_activate.html', context)

        from mail.management.commands.send_mail_notifications import send_mass_mail_html

        send_mass_mail_html([(subject, plain_text, html, settings.DEFAULT_FROM_EMAIL, [self.user.email])])
