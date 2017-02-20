# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.contrib.sites.models import Site
from registration.models import RegistrationProfile, RegistrationManager
from django.template.loader import render_to_string
from django.db.models import Q
from django.core.mail import send_mail
from mail.management.commands.send_mail_notifications import send_mass_mail_html

from django.contrib.auth.models import User
# from users.models import UserProfile

import datetime
import hashlib
import random
import logging

logger = logging.getLogger('django.request')


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
        elif len(users) == 1:
            return self.update_user(users[0]), False
        elif user_by_username and not (user_by_email | user_by_uid):
            new_username = self.generate_username()
            user = self.create_inactive_user(new_username, email, password, send_email)
            logger.info("Admission: User with email %s was created with generated login %s", user.email, user.username)
            return user, True
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


class AdmissionRegistrationProfile(RegistrationProfile):
    objects = AdmissionRegistrationProfileManager()

    def activation_key_expired(self):
        expiration_date = datetime.datetime.strptime(settings.ADMISSION_DATE_END, "%d.%m.%y %H:%M")
        return self.activation_key == self.ACTIVATED or \
               (expiration_date <= datetime.datetime.now())

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

        send_mass_mail_html([(subject, plain_text, html, settings.DEFAULT_FROM_EMAIL, [self.user.email])])
