# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.signals import m2m_changed

from datetime import datetime

from django.contrib.auth.models import User
from courses.models import Course
from groups.models import Group


class Message(models.Model):
    sender = models.ForeignKey(User, db_index=False, null=False, blank=False, related_name='sender+')
    recipients = models.ManyToManyField(User, db_index=False, null=False, blank=False, related_name='recipients+')
    recipients_user = models.ManyToManyField(User, db_index=False, null=True, blank=True,
                                             related_name='recipients_user+')
    recipients_group = models.ManyToManyField(Group, db_index=False, null=True, blank=True)
    recipients_course = models.ManyToManyField(Course, db_index=False, null=True, blank=True)

    title = models.CharField(max_length=191, db_index=False, null=True, blank=True)
    text = models.TextField(db_index=False, null=True, blank=True)

    create_time = models.DateTimeField(auto_now_add=True, default=datetime.now)

    def __unicode__(self):
        return u'%s %s' % (self.sender.username, self.title)

    def read_message(self, user):
        user_profile = user.get_profile()
        user_profile.unread_messages.remove(self)
        user_profile.send_notify_messages.remove(self)

    class Meta:
        ordering = ["-create_time"]


def make_unread_msg(sender, instance, action, **kwargs):
    if action in ["post_add", "post_remove"]:
        for user in instance.recipients.all():
            user_profile = user.get_profile()
            user_profile.unread_messages.add(instance)
            user_profile.send_notify_messages.add(instance)


m2m_changed.connect(make_unread_msg, sender=Message.recipients.through)
