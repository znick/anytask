# -*- coding: utf-8 -*-

from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
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


def set_user_info(user, user_info):
    user.first_name = user_info['first_name']
    user.last_name = user_info['last_name']
    user.save()

    user_profile = user.get_profile()
    user_profile.set_status(settings.FILIAL_STATUSES[user_info['filial']])
    user_profile.set_status(settings.ENROLLEE_STATUS)
    user_profile.phone = user_info['phone']

    user_profile.ya_contest_uid = user_info['uid']

    user_profile.ya_passport_uid = user_info['uid']
    user_profile.ya_passport_email = user_info['email']
    user_profile.ya_passport_login = user_info['login']
    if not user_info['is_updating']:
        user_profile.login_via_yandex = True

    user_profile.save()


@csrf_exempt
@require_POST
def register(request):
    if not ('HTTP_OAUTH' in request.META and request.META['HTTP_OAUTH'] == settings.YA_FORMS_OAUTH):
        return HttpResponseForbidden()

    post_data = request.POST.dict()

    username = request.META['HTTP_LOGIN']
    email = get_post_value(post_data, settings.YA_FORMS_FIELDS['email'])
    password = None
    new_user, registration_profile = AdmissionRegistrationProfile.objects.create_or_update_user(username, email,
                                                                                                password,
                                                                                                request=request)
    if new_user is not None:
        user_info = {
            'username': username,
            'email': email,
            'last_name': get_post_value(post_data, settings.YA_FORMS_FIELDS['last_name']),
            'first_name': get_post_value(post_data, settings.YA_FORMS_FIELDS['first_name']),
            'phone': get_post_value(post_data, settings.YA_FORMS_FIELDS['phone']),
            'filial': get_post_value(post_data, settings.YA_FORMS_FIELDS['filial']),
            'uid': request.META['HTTP_UID'],
            'is_updating': True if registration_profile else False
        }

        if user_info['is_updating']:
            registration_profile.user_info = json.dumps(user_info)
            registration_profile.save()
        else:
            set_user_info(new_user, user_info)

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
            logger.info("Activate user - %s %s", user.username, error_message)
            return contest_id

        logger.error("Activate user - Cant register user %s to contest %s. Error: %s", user.username, contest_id,
                     error_message)
        return False
    return contest_id


@never_cache
@require_GET
def activate(request, activation_key):
    context = {'info_title': _(u'Ошибка')}
    user, user_info = AdmissionRegistrationProfile.objects.activate_user(activation_key)
    if user:
        if user_info:
            set_user_info(user, json.loads(user_info))

        contest_id = contest_register(user)
        if contest_id:
            return HttpResponsePermanentRedirect(settings.CONTEST_URL + contest_id)
        else:
            context['info_text'] = _(u'Ошибка регистрации в Яндекс.Контесте.')
    else:
        context['info_text'] = _(u'Неверный код активации.')

    return render_to_response('info_page.html', context, context_instance=RequestContext(request))


@never_cache
@require_GET
def decline(request, activation_key):
    try:
        registration_profile = AdmissionRegistrationProfile.objects.decline_user(activation_key)

        if registration_profile:
            logger.info("Decline user - user %s requests deletion. Activation key %s",
                        registration_profile.user.username, registration_profile.activation_key)
        else:
            logger.warning("Decline user - wrong activation key %s", activation_key)
    except Exception as e:
        logger.error("Decline user - %s", e)

    context = {
        'info_title': _(u'Спасибо'),
        'info_text': _(u'Информация о Вас была удалена.'),
    }

    return render_to_response('info_page.html', context, context_instance=RequestContext(request))
