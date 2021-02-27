# -*- coding: utf-8 -*-

import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST, require_GET
from pytz import timezone as timezone_pytz

from courses.models import Course
from groups.models import Group
from mail.common import render_mail
from mail.models import Message
from users.model_user_status import get_statuses
from users.models import UserProfile

MONTH = {
    1: _(u"january"),
    2: _(u"february"),
    3: _(u"march"),
    4: _(u"april"),
    5: _(u"may"),
    6: _(u"june"),
    7: _(u"july"),
    8: _(u"august"),
    9: _(u"september"),
    10: _(u"october"),
    11: _(u"november"),
    12: _(u"december")
}


@require_GET
@login_required
def mail_page(request):
    user = request.user
    user_profile = user.profile

    users_from_staff_len = {}
    if user.is_staff and 'from_staff' in request.GET and 'user_ids_send_mail_counter' in request.session:
        key = 'user_ids_send_mail_' + request.GET['from_staff']
        if key in request.session:
            users_from_staff_len = {
                'index': request.GET['from_staff'],
                'length': len(request.session[key]),
            }

    if user.is_staff:
        courses_teacher = Course.objects.filter(is_active=True)
    else:
        courses_teacher = Course.objects.filter(teachers=user, is_active=True)

    context = {
        "user": user,
        "user_profile": user_profile,
        "courses_teacher": courses_teacher,
        'user_statuses': get_statuses(),
        "users_from_staff_len": users_from_staff_len,
        "snow_alert_message_fulltext": hasattr(settings, 'SEND_MESSAGE_FULLTEXT') and settings.SEND_MESSAGE_FULLTEXT,
    }

    return render(request, 'mail.html', context)


@require_GET
@login_required
def ajax_get_mailbox(request):
    response = dict()
    user = request.user
    user_profile = user.profile

    datatable_data = dict(request.GET)

    if "draw" not in datatable_data:
        return HttpResponseForbidden()

    if "make_read[]" in datatable_data:
        if datatable_data["make_read[]"][0] == "all":
            user_profile.unread_messages.clear()
            user_profile.send_notify_messages.clear()
        else:
            user_profile.unread_messages = list(
                user_profile.unread_messages
                .exclude(id__in=datatable_data["make_read[]"])
                .values_list("id", flat=True)
            )
            user_profile.send_notify_messages = list(
                user_profile.send_notify_messages
                .exclude(id__in=datatable_data["make_read[]"])
                .values_list("id", flat=True)
            )
    if "make_unread[]" in datatable_data:
        user_profile.unread_messages.add(*Message.objects.filter(id__in=datatable_data["make_unread[]"]))
    if "make_delete[]" in datatable_data:
        user_profile.deleted_messages.add(*Message.objects.filter(id__in=datatable_data["make_delete[]"]))
    if "make_undelete[]" in datatable_data:
        user_profile.deleted_messages = list(
            user_profile.deleted_messages
            .exclude(id__in=datatable_data["make_undelete[]"])
            .values_list("id", flat=True)
        )

    messages = Message.objects.none()
    messages_deleted = user_profile.deleted_messages.all()
    type_msg = datatable_data['type'][0]

    if type_msg == "inbox":
        messages = Message.objects.filter(recipients=user).exclude(id__in=messages_deleted)
    elif type_msg == "sent":
        messages = Message.objects.filter(sender=user).exclude(id__in=messages_deleted)
    elif type_msg == "trash":
        messages = messages_deleted

    data = list()
    start = int(datatable_data['start'][0])
    end = start + int(datatable_data['length'][0])
    unread = user_profile.unread_messages.all()
    for msg in messages[start:end]:
        data.append({
            "0": "",
            "1": u'%s %s' % (msg.sender.last_name, msg.sender.first_name),
            "2": msg.title,
            "3": format_date(msg.create_time.astimezone(timezone_pytz(user_profile.time_zone))),
            "DT_RowClass": "unread" if msg in unread else "",
            "DT_RowId": "row_msg_" + type_msg + "_" + str(msg.id),
            "DT_RowData": {
                "id": msg.id
            },
        })

    response['draw'] = datatable_data['draw']
    response['recordsTotal'] = messages.count()
    response['recordsFiltered'] = messages.count()
    response['data'] = data
    response['unread_count'] = user_profile.get_unread_count()
    response['type'] = type_msg

    return HttpResponse(json.dumps(response),
                        content_type="application/json")


def format_date(date):
    date_str = ""
    now = timezone.now()
    if now.year == date.year:
        if now.day == date.day and now.month == date.month:
            date_str = date.strftime("%H:%M")
        else:
            date_str = str(date.day) + u" " + MONTH[date.month]
    else:
        date_str = date.strftime("%d.%m.%y")

    return date_str


@require_GET
@login_required
def ajax_get_message(request):
    response = dict()
    user = request.user
    user_profile = user.profile

    if "msg_id" not in request.GET:
        return HttpResponseForbidden()

    msg_id = int(request.GET["msg_id"])
    message = Message.objects.get(id=msg_id)

    if message.sender != user and user not in message.recipients.all():
        return HttpResponseForbidden()

    unread_count = int(request.GET["unread_count"])
    if message in user_profile.unread_messages.all():
        message.read_message(user)
        unread_count -= 1

    recipients_user = []
    recipients_group = []
    recipients_course = []
    recipients_status = []

    if message.hidden_copy and message.sender != user:
        recipients_user.append({
            "id": user.id,
            "fullname": u'%s %s' % (user.last_name, user.first_name),
            "url": user.get_absolute_url()
        })
    else:
        for recipient in message.recipients_user.all():
            recipients_user.append({
                "id": recipient.id,
                "fullname": u'%s %s' % (recipient.last_name, recipient.first_name),
                "url": recipient.get_absolute_url()
            })
        for group in message.recipients_group.all():
            recipients_group.append({
                "id": group.id,
                "name": group.name
            })
        for course in message.recipients_course.all():
            recipients_course.append({
                "id": course.id,
                "name": course.name,
                "url": course.get_absolute_url(),
            })
        for status in message.recipients_status.all():
            recipients_status.append({
                "id": status.id,
                "name": status.name
            })

    if message.sender != user or request.GET["mailbox"] == 'inbox':
        text = render_mail(message, user)
    else:
        text = message.text

    response['sender'] = {
        "id": message.sender.id,
        "fullname": u'%s %s' % (message.sender.last_name, message.sender.first_name),
        "url": message.sender.get_absolute_url(),
        "avatar": message.sender.profile.avatar.url if message.sender.profile.avatar else "",
    }
    response['recipients_user'] = recipients_user
    response['recipients_group'] = recipients_group
    response['recipients_course'] = recipients_course
    response['recipients_status'] = recipients_status
    response['date'] = message.create_time.astimezone(timezone_pytz(user_profile.time_zone))\
        .strftime("%d.%m.%y %H:%M:%S")
    response['text'] = text
    response['unread_count'] = unread_count

    return HttpResponse(json.dumps(response),
                        content_type="application/json")


@require_POST
@login_required
def ajax_send_message(request):
    user = request.user

    data = dict(request.POST)

    hidden_copy = False
    if 'hidden_copy' in data and data['hidden_copy'][0]:
        hidden_copy = True

    variable = False
    if 'variable' in data and data['variable'][0]:
        variable = True

    message = Message()
    message.sender = user
    message.title = data['new_title'][0]
    message.text = data['new_text'][0]
    message.hidden_copy = hidden_copy
    message.variable = variable
    message.save()

    recipients_ids = set()

    if "new_recipients_user[]" in data or "new_recipients_preinit[]" in data:
        users = data.get("new_recipients_user[]", [])
        if "new_recipients_preinit[]" in data:
            users += request.session.get('user_ids_send_mail_' + data["new_recipients_preinit[]"][0], [])
        message.recipients_user = users
        recipients_ids.update(message.recipients_user.values_list('id', flat=True))

    group_ids = []
    if "new_recipients_group[]" in data:
        message.recipients_group = data["new_recipients_group[]"]

        for group in Group.objects.filter(id__in=data["new_recipients_group[]"]):
            recipients_ids.update(group.students.exclude(id=user.id).values_list('id', flat=True))
            group_ids.append(group.id)

    if "new_recipients_course[]" in data:
        message.recipients_course = data["new_recipients_course[]"]

        for course in Course.objects.filter(id__in=data["new_recipients_course[]"]):
            for group in course.groups.exclude(id__in=group_ids).distinct():
                recipients_ids.update(group.students.exclude(id=user.id).values_list('id', flat=True))

    if "new_recipients_status[]" in data:
        message.recipients_status = data["new_recipients_status[]"]

        recipients_ids.update(UserProfile.objects.filter(user_status__in=data["new_recipients_status[]"])
                              .values_list('user__id', flat=True))

    message.recipients = list(recipients_ids)

    return HttpResponse("OK")
