# -*- coding: utf-8 -*-

from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.http import HttpResponse, HttpResponseForbidden, HttpResponsePermanentRedirect
from django.conf import settings
from django.shortcuts import render

from anycontest.common import user_register_to_contest

from admission.models import AdmissionRegistrationProfile

import json
import logging
import datetime

logger = logging.getLogger('django.request')

ANOTHER = u'Другое'
YES = u'Да'
MONTH = {
    u'января': 1,
    u'февраля': 2,
    u'марта': 3,
    u'апреля': 4,
    u'мая': 5,
    u'июня': 6,
    u'июля': 7,
    u'августа': 8,
    u'сентября': 9,
    u'октября': 10,
    u'ноября': 11,
    u'декабря': 12
}


def get_post_value(post_data, key):
    return json.loads(post_data[key])['value']


def get_post_question(post_data, key):
    return json.loads(post_data[key])['question']['label']['ru']


def set_user_info(user, user_info):
    user.first_name = user_info['first_name']
    user.last_name = user_info['last_name']
    user.email = user_info['email']
    user.save()

    user_profile = user.profile
    user_profile.set_status(settings.FILIAL_STATUSES[user_info['filial']])
    user_profile.set_status(settings.ENROLLEE_STATUS)
    user_profile.middle_name = user_info['middle_name']

    birth_date_split = user_info['birth_date'][:-3].split()
    user_profile.birth_date = datetime.datetime(
        int(birth_date_split[2]),
        MONTH[birth_date_split[1]],
        int(birth_date_split[0])
    )

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
    uid = request.META['HTTP_UID']
    new_user, registration_profile = AdmissionRegistrationProfile.objects.create_or_update_user(username, email,
                                                                                                password, uid,
                                                                                                send_email=False,
                                                                                                request=request)
    if new_user is not None and registration_profile is not None:
        user_info = {
            'username': username,
            'uid': uid,
            'ya_email': '',
            'is_updating': registration_profile.is_updating
        }
        if request.META['HTTP_EMAIL'] and request.META['HTTP_EMAIL'] != 'None':
            user_info['ya_email'] = request.META['HTTP_EMAIL']

        for key, post_data_key in settings.YA_FORMS_FIELDS.items():
            user_info[key] = get_post_value(post_data, post_data_key)

        for key, post_data_keys in settings.YA_FORMS_FIELDS_ADDITIONAL.items():
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

    got_info, response_text = user_register_to_contest(contest_id, user.profile.ya_contest_uid)

    if not got_info:
        if response_text == 'User already registered for contest':
            logger.info("Activate user - %s %s", user.username, response_text)
            return contest_id

        logger.error("Activate user - Cant register user %s to contest %s. Error: %s", user.username, contest_id,
                     response_text)
        return False

    logger.info("Activate user - user %s was successfully registered to contest %s.", user.username, contest_id)
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
            return HttpResponsePermanentRedirect(settings.CONTEST_URL + 'contest/' + str(contest_id))
        else:
            context['info_text'] = _(u'oshibka_registracii_v_contest')
    else:
        context['info_text'] = _(u'nevernyy_kod_aktivatsii')

    return render(request, 'info_page.html', context)


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

    return render(request, 'info_page.html', context)
