# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.auth.models import User
from mail.models import Message
from courses.models import Course
from groups.models import Group
from years.models import Year

from django.core.urlresolvers import reverse
from mail.views import format_date
from pytz import timezone as timezone_pytz
import json

import mail.views


class CreateTest(TestCase):
    def setUp(self):
        self.sender_password = 'password'
        self.sender = User.objects.create_user(
            username='sender', password=self.sender_password)

        self.recipients_password = 'password'
        self.recipients = [User.objects.create_user(
            username='recipients', password=self.recipients_password)]

        self.year = Year.objects.create(start_year=2016)

        self.recipients_course = [Course.objects.create(name='course_name',
                                                        year=self.year)]

        self.recipients_group = [Group.objects.create(name='group_name',
                                                      year=self.year)]

    def test_message_create_filled(self):
        message = Message()

        message.sender = self.sender
        message.title = u"title"
        message.text = u"text"

        message.save()

        message.recipients = self.recipients
        message.recipients_user = self.recipients
        message.recipients_course = self.recipients_course
        message.recipients_group = self.recipients_group

        message_id = message.id

        message = Message.objects.get(id=message_id)

        self.assertIsInstance(message, Message)
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.title, u"title")
        self.assertEqual(message.text, u"text")
        self.assertCountEqual(message.recipients.all(), self.recipients)
        self.assertCountEqual(message.recipients_user.all(), self.recipients)
        self.assertCountEqual(message.recipients_course.all(), self.recipients_course)
        self.assertCountEqual(message.recipients_group.all(), self.recipients_group)


class ViewsTest(TestCase):
    def setUp(self):
        self.sender_password = 'password'
        self.sender = User.objects.create_user(
            username='sender', password=self.sender_password)

        self.user_password = 'password'
        self.user = User.objects.create_user(
            username='user', password=self.user_password)

        self.user_in_group_password = 'password'
        self.user_in_group = User.objects.create_user(
            username='user_in_group', password=self.user_in_group_password)

        self.user_in_course_password = 'password'
        self.user_in_course = User.objects.create_user(
            username='user_in_course', password=self.user_in_course_password)

        self.year = Year.objects.create(start_year=2016)

        self.recipients_user = [self.user]

        self.recipients_group = [Group.objects.create(name='group1_name',
                                                      year=self.year)]
        self.recipients_group[0].students = [self.user_in_group]

        self.recipients_course = [Course.objects.create(name='course_name',
                                                        year=self.year)]
        self.group_in_course = Group.objects.create(name='group2_name',
                                                    year=self.year)
        self.group_in_course.students = [self.user_in_course]
        self.recipients_course[0].groups = [self.group_in_course]

        self.recipients = [self.user, self.user_in_group, self.user_in_course]

        self.recipients_password = {
            self.user.username: self.user_password,
            self.user_in_group.username: self.user_in_group_password,
            self.user_in_course.username: self.user_in_course_password
        }

    def test_mail_page_anonymously(self):
        client = self.client

        # get page
        response = client.get(reverse(mail.views.mail_page))
        self.assertEqual(response.status_code, 302)

    def test_ajax_get_mailbox_anonymously(self):
        client = self.client

        # get page
        response = client.get(reverse(mail.views.ajax_get_mailbox))
        self.assertEqual(response.status_code, 302)

    def test_ajax_get_message_anonymously(self):
        client = self.client

        # get page
        response = client.get(reverse(mail.views.ajax_get_message))
        self.assertEqual(response.status_code, 302)

    def test_ajax_send_message_anonymously(self):
        client = self.client

        # get page
        response = client.get(reverse(mail.views.ajax_send_message))
        self.assertEqual(response.status_code, 405)

    def test_mail_page_with_user(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.sender.username, password=self.sender_password))

        # get page
        response = client.get(reverse(mail.views.mail_page))
        self.assertEqual(response.status_code, 200)

    def test_ajax_get_mailbox_user(self):
        client = self.client

        get_data = {
            u'draw': 1,
            u'start': 0,
            u'length': 10,
            u'type': u'inbox'
        }

        response_data = {
            u'draw': [u'1'],
            u'recordsTotal': 0,
            u'data': [],
            u'recordsFiltered': 0,
            u'unread_count': 0,
            u'type': u'inbox'
        }

        # login
        self.assertTrue(client.login(username=self.sender.username, password=self.sender_password))

        # get page
        response = client.get(reverse(mail.views.ajax_get_mailbox), get_data)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.content), response_data)

    def test_ajax_get_message_user(self):
        client = self.client

        message = Message()
        message.sender = self.sender
        message.title = u"title"
        message.text = u"text"
        message.save()
        message.recipients = self.recipients
        message.recipients_user = self.recipients_user
        message.recipients_group = self.recipients_group
        message.recipients_course = self.recipients_course

        get_data = {
            u'unread_count': 0,
            u'msg_id': 1,
            u'mailbox': 'inbox'
        }

        response_data = {
            'sender': {
                'url': self.sender.get_absolute_url(),
                'fullname': u'%s %s' % (self.sender.last_name, self.sender.first_name),
                'id': self.sender.id,
                'avatar': ''
            },
            'unread_count': 0,
            'text': message.text,
            'date': message.create_time.astimezone(
                timezone_pytz(self.sender.profile.time_zone)
            ).strftime("%d.%m.%y %H:%M:%S"),
            'recipients_course': [{
                'url': self.recipients_course[0].get_absolute_url(),
                'name': self.recipients_course[0].name,
                'id': self.recipients_course[0].id
            }],
            'recipients_group': [{
                'name': self.recipients_group[0].name,
                'id': self.recipients_group[0].id
            }],
            'recipients_user': [{
                'url': self.recipients_user[0].get_absolute_url(),
                'fullname': u'%s %s' % (self.recipients_user[0].last_name, self.recipients_user[0].first_name),
                'id': self.recipients_user[0].id
            }],
            'recipients_status': []
        }

        # login
        self.assertTrue(client.login(username=self.sender.username, password=self.sender_password))

        # get page
        response = client.get(reverse(mail.views.ajax_get_message), get_data)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(json.loads(response.content), response_data)

    def check_empty_mailboxes(self, mailboxes, unread_count=0):
        for mailbox in mailboxes:
            get_data = {
                u'draw': 1,
                u'start': 0,
                u'length': 10,
                u'type': mailbox
            }

            response_data = {
                u'draw': [u'1'],
                u'recordsTotal': 0,
                u'data': [],
                u'recordsFiltered': 0,
                u'unread_count': unread_count,
                u'type': mailbox
            }

            # get page
            response = self.client.get(reverse(mail.views.ajax_get_mailbox), get_data)
            self.assertEqual(response.status_code, 200)
            self.assertDictEqual(json.loads(response.content), response_data)

    def test_ajax_send_message_user(self):
        client = self.client

        post_data = {
            u'new_title': u'title',
            u'new_text': u'text',
            u'new_recipients_course[]': [self.recipients_course[0].id],
            u'new_recipients_group[]': [self.recipients_group[0].id],
            u'new_recipients_user[]': [self.recipients_user[0].id]
        }

        # login
        self.assertTrue(client.login(username=self.sender.username, password=self.sender_password))

        # get page
        response = client.post(reverse(mail.views.ajax_send_message), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'OK')

        # check msg creation
        messages_count = Message.objects.count()
        self.assertEqual(messages_count, 1)
        message = Message.objects.get(id=1)
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.title, u"title")
        self.assertEqual(message.text, u"text")
        self.assertCountEqual(message.recipients.all(), self.recipients)
        self.assertCountEqual(message.recipients_user.all(), self.recipients_user)
        self.assertCountEqual(message.recipients_course.all(), self.recipients_course)
        self.assertCountEqual(message.recipients_group.all(), self.recipients_group)

        # check sent sender
        get_data = {
            u'draw': 1,
            u'start': 0,
            u'length': 10,
            u'type': u'sent'
        }

        response_data = {
            u'draw': [u'1'],
            u'recordsTotal': messages_count,
            u'data': [{
                u'0': u'',
                u'1': u'%s %s' % (message.sender.last_name, message.sender.first_name),
                u'2': message.title,
                u'3': format_date(message.create_time.astimezone(timezone_pytz(self.sender.profile.time_zone))),
                u'DT_RowClass': u'',
                u'DT_RowData': {u'id': 1},
                u'DT_RowId': u'row_msg_sent_' + str(message.id)
            }],
            u'recordsFiltered': messages_count,
            u'unread_count': 0,
            u'type': u'sent'
        }

        # get page
        response = client.get(reverse(mail.views.ajax_get_mailbox), get_data)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.content), response_data)

        for recipient in self.recipients:
            # check inbox
            get_data = {
                u'draw': 1,
                u'start': 0,
                u'length': 10,
                u'type': u'inbox'
            }

            response_data = {
                u'draw': [u'1'],
                u'recordsTotal': messages_count,
                u'data': [{
                    u'0': u'',
                    u'1': u'%s %s' % (message.sender.last_name, message.sender.first_name),
                    u'2': message.title,
                    u'3': format_date(
                        message.create_time.astimezone(timezone_pytz(recipient.profile.time_zone))
                    ),
                    u'DT_RowClass': u'unread',
                    u'DT_RowData': {u'id': 1},
                    u'DT_RowId': u'row_msg_inbox_' + str(message.id)
                }],
                u'recordsFiltered': messages_count,
                u'unread_count': 1,
                u'type': u'inbox'
            }

            # login
            self.assertTrue(client.login(username=recipient.username,
                                         password=self.recipients_password[recipient.username]))

            # get page
            response = client.get(reverse(mail.views.ajax_get_mailbox), get_data)
            self.assertEqual(response.status_code, 200)
            self.assertDictEqual(json.loads(response.content), response_data)

            # check other mailboxes recipient
            self.check_empty_mailboxes([u"sent", u"trash"], 1)

    def test_message_manipulation(self):
        client = self.client
        recipient = self.recipients[0]

        post_data = {
            u'new_title': u'title',
            u'new_text': u'text',
            u'new_recipients_user[]': [self.recipients_user[0].id]
        }

        # login
        self.assertTrue(client.login(username=self.sender.username, password=self.sender_password))

        # get page
        response = client.post(reverse(mail.views.ajax_send_message), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'OK')

        message = Message.objects.get(id=1)

        # have unread msg
        for recipient in message.recipients.all():
            self.assertCountEqual(recipient.profile.unread_messages.all(), [message])

        # make read
        get_data = {
            u'draw': 1,
            u'start': 0,
            u'length': 10,
            u'make_read[]': [message.id],
            u'type': u'inbox'
        }

        response_data = {
            u'draw': [u'1'],
            u'recordsTotal': 1,
            u'data': [{
                u'0': u'',
                u'1': u'%s %s' % (message.sender.last_name, message.sender.first_name),
                u'2': message.title,
                u'3': format_date(message.create_time.astimezone(timezone_pytz(recipient.profile.time_zone))),
                u'DT_RowClass': u'',
                u'DT_RowData': {u'id': 1},
                u'DT_RowId': u'row_msg_inbox_' + str(message.id)
            }],
            u'recordsFiltered': 1,
            u'unread_count': 0,
            u'type': u'inbox'
        }

        # login
        self.assertTrue(client.login(username=recipient.username,
                                     password=self.recipients_password[recipient.username]))

        # get page
        response = client.get(reverse(mail.views.ajax_get_mailbox), get_data)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.content), response_data)

        # make unread
        get_data = {
            u'draw': 1,
            u'start': 0,
            u'length': 10,
            u'make_unread[]': [message.id],
            u'type': u'inbox'
        }

        response_data = {
            u'draw': [u'1'],
            u'recordsTotal': 1,
            u'data': [{
                u'0': u'',
                u'1': u'%s %s' % (message.sender.last_name, message.sender.first_name),
                u'2': message.title,
                u'3': format_date(
                    message.create_time.astimezone(timezone_pytz(recipient.profile.time_zone))
                ),
                u'DT_RowClass': u'unread',
                u'DT_RowData': {u'id': 1},
                u'DT_RowId': u'row_msg_inbox_' + str(message.id)
            }],
            u'recordsFiltered': 1,
            u'unread_count': 1,
            u'type': u'inbox'
        }

        # get page
        response = client.get(reverse(mail.views.ajax_get_mailbox), get_data)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.content), response_data)

        # delete
        get_data = {
            u'draw': 1,
            u'start': 0,
            u'length': 10,
            u'make_delete[]': [message.id],
            u'type': u'trash'
        }

        response_data = {
            u'draw': [u'1'],
            u'recordsTotal': 1,
            u'data': [{
                u'0': u'',
                u'1': u'%s %s' % (message.sender.last_name, message.sender.first_name),
                u'2': message.title,
                u'3': format_date(
                    message.create_time.astimezone(timezone_pytz(recipient.profile.time_zone))
                ),
                u'DT_RowClass': u'unread',
                u'DT_RowData': {u'id': 1},
                u'DT_RowId': u'row_msg_trash_' + str(message.id)
            }],
            u'recordsFiltered': 1,
            u'unread_count': 0,
            u'type': u'trash'
        }

        # get page
        response = client.get(reverse(mail.views.ajax_get_mailbox), get_data)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.content), response_data)

        # check other mailboxes recipient
        self.check_empty_mailboxes([u"inbox", u"sent"])

        # undelete
        get_data = {
            u'draw': 1,
            u'start': 0,
            u'length': 10,
            u'make_undelete[]': [message.id],
            u'type': u'inbox'
        }

        response_data = {
            u'draw': [u'1'],
            u'recordsTotal': 1,
            u'data': [{
                u'0': u'',
                u'1': u'%s %s' % (message.sender.last_name, message.sender.first_name),
                u'2': message.title,
                u'3': format_date(
                    message.create_time.astimezone(timezone_pytz(recipient.profile.time_zone))
                ),
                u'DT_RowClass': u'unread',
                u'DT_RowData': {u'id': 1},
                u'DT_RowId': u'row_msg_inbox_' + str(message.id)
            }],
            u'recordsFiltered': 1,
            u'unread_count': 1,
            u'type': u'inbox'
        }

        # get page
        response = client.get(reverse(mail.views.ajax_get_mailbox), get_data)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(json.loads(response.content), response_data)

        # check other mailboxes recipient
        self.check_empty_mailboxes([u"sent", u"trash"], 1)
