# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext

from django.contrib.auth.models import User
from mail.models import Message
from courses.models import Course
from groups.models import Group

import json
import datetime

MONTH = {
    1: u"янв.",
    2: u"февр.",
    3: u"мар.",
    4: u"апр.",
    5: u"мая",
    6: u"июн.",
    7: u"июл.",
    8: u"авг.",
    9: u"сент.",
    10: u"окт.",
    11: u"нояб.",
    12: u"дек."
}


@login_required
def mail_page(request):
    user = request.user
    user_profile = user.get_profile()

    if user.is_staff:
        courses_teacher = Course.objects.filter(is_active=True)
    else:
        courses_teacher = Course.objects.filter(teachers=user, is_active=True)

    context = {
        "user_profile": user_profile,
        "courses_teacher": courses_teacher
    }

    return render_to_response('mail.html', context, context_instance=RequestContext(request)    )


@login_required
def ajax_get_mailbox(request):
    response = dict()
    user = request.user
    user_profile = user.get_profile()

    if request.method != "GET":
        return HttpResponseForbidden()

    datatable_data = dict(request.GET)

    if "draw" not in datatable_data:
        return HttpResponseForbidden()

    if "make_read[]" in datatable_data:
        if datatable_data["make_read[]"][0] == "all":
            user_profile.unread_messages.clear()
        else:
            user_profile.unread_messages.remove(*Message.objects.filter(id__in=datatable_data["make_read[]"]))
    if "make_unread[]" in datatable_data:
        user_profile.unread_messages.add(*Message.objects.filter(id__in=datatable_data["make_unread[]"]))
    if "make_delete[]" in datatable_data:
        user_profile.deleted_messages.add(*Message.objects.filter(id__in=datatable_data["make_delete[]"]))
    if "make_undelete[]" in datatable_data:
        user_profile.deleted_messages.remove(*Message.objects.filter(id__in=datatable_data["make_undelete[]"]))

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
            "3": format_date(msg.create_time),
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
    now = datetime.datetime.now()

    if now.year == date.year:
        if now.day == date.day:
            date_str = date.strftime("%H:%M")
        else:
            date_str = unicode(date.day) + u" " + MONTH[date.month]
    else:
        date_str = date.strftime("%d.%m.%y")

    return date_str


@login_required
def ajax_get_message(request):
    response = dict()
    user = request.user
    user_profile = user.get_profile()

    if request.method != "GET":
        return HttpResponseForbidden()

    if "msg_id" not in request.GET:
        return HttpResponseForbidden()

    msg_id = int(request.GET["msg_id"])
    message = Message.objects.get(id=msg_id)
    recipients = message.recipients.all()

    if message.sender != user and user not in message.recipients.all():
        return HttpResponseForbidden()

    unread_count = int(request.GET["unread_count"])
    if message in user_profile.unread_messages.all():
        user_profile.unread_messages.remove(message)
        unread_count -= 1

    recipients_data = []
    for recipient in recipients:
        recipients_data.append(get_user_info(recipient))

    response['sender'] = get_user_info(message.sender)
    response['recipients'] = recipients_data
    response['date'] = message.create_time.strftime("%d.%m.%y %H:%M:%S")
    response['text'] = message.text
    response['unread_count'] = unread_count

    return HttpResponse(json.dumps(response),
                        content_type="application/json")


def get_user_info(user):
    return {
        "fullname": u'%s %s' % (user.last_name, user.first_name),
        "url": user.get_absolute_url(),
        "avatar": user.get_profile().avatar.url if user.get_profile().avatar else "",
    }


@login_required
def ajax_send_message(request):
    response = dict()
    user = request.user
    user_profile = user.get_profile()

    if request.method != "POST":
        return HttpResponseForbidden()

    data = dict(request.POST)

    message = Message()
    message.sender = user
    message.title = data['new_title'][0]
    message.text = data['new_text'][0]
    message.save()

    if "new_recipients_user[]" in data:
        message.recipients.add(*User.objects.filter(id__in=data["new_recipients_user[]"]))

    group_ids = []
    if "new_recipients_group[]" in data:
        for group in Group.objects.filter(id__in=data["new_recipients_group[]"]):
            message.recipients.add(*group.students.exclude(id=user.id))
            group_ids.append(group.id)

    if "new_recipients_course[]" in data:
        for course in Course.objects.filter(id__in=data["new_recipients_course[]"]):
            for group in course.groups.all():
                if group.id not in group_ids:
                    message.recipients.add(*group.students.exclude(id=user.id))
                    group_ids.append(group.id)


    return HttpResponse(json.dumps(response),
                        content_type="application/json")
