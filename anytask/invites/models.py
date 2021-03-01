# encoding: utf-8
from django.db import models


from django.contrib.auth.models import User

from courses.models import Course
from groups.models import Group

import random
import string

from django.db import IntegrityError


class Invite(models.Model):
    generated_by = models.ForeignKey(User, db_index=False, null=False, blank=False, related_name='invite_generated_by')
    group = models.ForeignKey(Group, db_index=False, null=True, blank=True)
    invited_users = models.ManyToManyField(User, blank=True)

    key = models.CharField(max_length=10, db_index=True, null=False, blank=False, unique=True)

    added_time = models.DateTimeField(auto_now_add=True)  # remove default=timezone.now
    update_time = models.DateTimeField(auto_now=True)  # remove default=timezone.now

    def __unicode__(self):
        return u"{0}".format(self.key)

    @staticmethod
    def user_can_generate_invite(generative_user):
        if generative_user.is_anonymous():
            return False

        if generative_user.is_superuser:
            return True

        if Course.objects.filter(teachers=generative_user).count():
            return True

        return False

    @staticmethod
    def generate_invite(generated_by, group, size=7):
        invite = Invite()
        invite.generated_by = generated_by
        invite.group = group
        key = Invite._id_generator(size)
        for _ in xrange(1000):
            try:
                if Invite.objects.filter(key=key).count():
                    key = Invite._id_generator(size)
                else:
                    invite.key = key
                    invite.save()
                    return invite
            except IntegrityError:
                return Invite.generate_invite(generated_by, group, size)

    @staticmethod
    def generate_invites(count, generated_by, group, size=7):
        for _ in xrange(count):
            yield Invite.generate_invite(generated_by, group, size)

    @staticmethod
    def _id_generator(size=7, chars=string.ascii_letters + string.digits):
        return ''.join(random.choice(chars) for x in range(size))
