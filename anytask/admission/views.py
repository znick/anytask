# -*- coding: utf-8 -*-

from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.http import HttpResponse, HttpResponseForbidden, HttpResponsePermanentRedirect
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext

from admission.models import AdmissionRegistrationProfile

import json
import requests
import logging

logger = logging.getLogger('django.request')


def get_post_value(post_data, key):
    return json.loads(post_data[key])['value']


@csrf_exempt
@require_POST
def register(request):
    if not ('HTTP_OAUTH' in request.META and request.META['HTTP_OAUTH'] == settings.YA_FORMS_OAUTH):
        return HttpResponseForbidden()

    post_data = request.POST.dict()

    username = request.META['HTTP_LOGIN']
    email = get_post_value(post_data, settings.YA_FORMS_FIELDS['email'])
    password = None
    new_user, is_created = AdmissionRegistrationProfile.objects.create_or_update_user(username, email, password,
                                                                                      request=request)
    if new_user is not None:
        last_name = get_post_value(post_data, settings.YA_FORMS_FIELDS['last_name'])
        first_name = get_post_value(post_data, settings.YA_FORMS_FIELDS['first_name'])
        new_user.first_name = first_name
        new_user.last_name = last_name
        new_user.save()

        new_user_profile = new_user.get_profile()
        new_user_profile.set_status(
            settings.FILIAL_STATUSES[get_post_value(post_data, settings.YA_FORMS_FIELDS['filial'])]
        )
        new_user_profile.set_status(settings.ENROLLEE_STATUS)
        if is_created:
            new_user_profile.login_via_yandex = True
        if not new_user_profile.ya_passport_uid:
            new_user_profile.ya_passport_uid = request.META['HTTP_UID']
        if not new_user_profile.ya_contest_uid:
            new_user_profile.ya_contest_uid = request.META['HTTP_UID']
        new_user_profile.save()

    return HttpResponse("OK")


def contest_register(user):
    contest_id = settings.ADMISSION_CONTESTS[user.email.__hash__() % len(settings.ADMISSION_CONTESTS)]

    req = requests.get(
        settings.CONTEST_API_URL + 'register-user?uidToRegister=' + str(user.get_profile().ya_contest_uid) +
        '&contestId=' + str(contest_id),
        headers={'Authorization': 'OAuth ' + settings.CONTEST_OAUTH})

    if 'error' in req.json():
        error_message = req.json()["error"]["message"]
        if error_message == 'User already registered for contest':
            return contest_id

        logger.error("Cant register user %s to contest %s. Error: %s", user.username, contest_id, error_message)
        return False
    return contest_id


@require_GET
def activate(request, activation_key):
    context = {}
    user = AdmissionRegistrationProfile.objects.activate_user(activation_key)
    if user:
        contest_id = contest_register(user)
        if contest_id:
            return HttpResponsePermanentRedirect(settings.CONTEST_URL + contest_id)
        else:
            context['error_text'] = _(u'Ошибка регистрации в Яндекс.Контесте.')
    else:
        context['error_text'] = _(u'Неверный код активации.')

    return render_to_response('error_page.html', context, context_instance=RequestContext(request))
