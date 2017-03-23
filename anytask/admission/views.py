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
import locale
import datetime

logger = logging.getLogger('django.request')


def get_post_value(post_data, key):
    return json.loads(post_data[key])['value']


def get_post_question(post_data, key):
    return json.loads(post_data[key])['question']['label']['ru']


def set_user_info(user, user_info):
    ANOTHER = u'Другое'
    YES = u'Да'

    user.first_name = user_info['first_name']
    user.last_name = user_info['last_name']
    user.save()

    user_profile = user.get_profile()
    user_profile.set_status(settings.FILIAL_STATUSES[user_info['filial']])
    user_profile.set_status(settings.ENROLLEE_STATUS)
    user_profile.middle_name = user_info['middle_name']

    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
    user_profile.birth_date = datetime.datetime.strptime(user_info['birth_date'][:-3].encode('utf-8'), "%d %B %Y")

    user_profile.phone = user_info['phone']
    user_profile.city_of_residence = user_info['city_of_residence']

    if user_info['university'] == ANOTHER:
        user_profile.university = user_info['university_text']
    else:
        user_profile.university = user_info['university']

    if user_info['university_in_process'] == YES:
        user_profile.university_in_process = True
    else:
        user_profile.university_in_process = False

    if user_info['university_class'] == ANOTHER:
        user_profile.university_class = user_info['university_class_text']
    else:
        user_profile.university_class = user_info['university_class']

    user_profile.university_department = user_info['university_department']
    user_profile.university_year_end = user_info['university_year_end']
    user_profile.additional_info = user_info['additional_info']

    user_profile.ya_contest_uid = user_info['uid']
    user_profile.ya_contest_login = user_info['username']

    user_profile.ya_passport_uid = user_info['uid']
    user_profile.ya_passport_email = user_info['ya_email']
    user_profile.ya_passport_login = user_info['username']

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
                                                                                                send_email=False,
                                                                                                request=request)
    if new_user is not None and registration_profile is not None:
        user_info = {
            'username': username,
            'uid': request.META['HTTP_UID'],
            'ya_email': request.META['HTTP_EMAIL'],
            'is_updating': registration_profile.is_updating
        }

        for key, post_data_key in settings.YA_FORMS_FIELDS.iteritems():
            user_info[key] = get_post_value(post_data, post_data_key)

        for key, post_data_keys in settings.YA_FORMS_FIELDS_ADDITIONAL.iteritems():
            info_json = []
            for post_data_key in post_data_keys:
                info_json.append({
                    'question': get_post_question(post_data, post_data_key),
                    'value': get_post_value(post_data, post_data_key)
                })
            user_info[key] = json.dumps(info_json)

        registration_profile.user_info = json.dumps(user_info)
        registration_profile.save()

        if not registration_profile.is_updating:
            set_user_info(new_user, user_info)

        registration_profile.send_activation_email()

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
    context = {'info_title': _(u'oshibka')}
    user, user_info = AdmissionRegistrationProfile.objects.activate_user(activation_key)
    if user:
        if user_info:
            set_user_info(user, json.loads(user_info))

        contest_id = contest_register(user)
        if contest_id:
            return HttpResponsePermanentRedirect(settings.CONTEST_URL + contest_id)
        else:
            context['info_text'] = _(u'oshibka_registracii_v_contest')
    else:
        context['info_text'] = _(u'nevernyy_kod_aktivatsii')

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
        'info_title': _(u'spasibo'),
        'info_text': _(u'informatsiya_o_vas_byla_udalena'),
    }

    return render_to_response('info_page.html', context, context_instance=RequestContext(request))
