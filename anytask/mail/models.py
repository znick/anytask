# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.signals import m2m_changed

from datetime import datetime

from django.contrib.auth.models import User

#
# class Dialog(models.Model):
#     author = models.ForeignKey(User, db_index=True, null=False, blank=False, related_name='author')
#     recipients = models.ManyToManyField(User, db_index=False, null=False, blank=False, related_name='recipients')
#
#     deleted = models.BooleanField(db_index=False, null=False, blank=False, default=False)
#     create_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
#

class Message(models.Model):
    # dialog = models.ForeignKey(Dialog, db_index=True, null=False, blank=False)
    sender = models.ForeignKey(User, db_index=False, null=False, blank=False)
    recipients = models.ManyToManyField(User, db_index=False, null=False, blank=False, related_name='recipients')

    title = models.CharField(max_length=191, db_index=False, null=True, blank=True)
    text = models.TextField(db_index=False, null=True, blank=True)

    is_important = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    create_time = models.DateTimeField(auto_now_add=True, default=datetime.now)

    def __unicode__(self):
        return u'%s %s' % (self.sender.username, self.title)

    def make_unread(self, users=None):
        if users is None:
            users = self.recipients.all()
        elif not hasattr(users, '__iter__'):
            users = [users]

        for user in users:
            user.get_profile().unread_messages.add(self)

    def make_read(self, user):
        user.get_profile().unread_messages.remove(self)

    class Meta:
        ordering = ["-create_time"]


def make_unread_msg(sender, instance, action, **kwargs):
    if action in ["post_add", "post_remove"]:
        instance.make_unread()

m2m_changed.connect(make_unread_msg, sender=Message.recipients.through)
