# -*- coding: utf-8 -*-

from django.utils.translation import ugettext as _
from django.contrib.auth.models import Permission

PERMS_CLASSES = {
    'users': ['userprofileuserobjectpermission'],
    'schools': ['schooluserobjectpermission'],
    'courses': ['courseuserobjectpermission'],
    'groups': ['groupuserobjectpermission'],
}

LOCALE_PERMS_APP_NAMES = {
    'users': _(u'dostupy_uchetnoy_zapisi'),
    'schools': _(u'dostupy_v_shkolakh'),
    'courses': _(u'dostupy_v_kursakh'),
    'groups': _(u'dostupy_v_gruppakh'),
}

LOCALE_PERMS_NAMES = {
    'users': {
        'view_backoffice_page': _(u'prosmotr_backoffice'),
    },
    'schools': {
        'view_permissions': _(u'prosmotr_dostupov'),
        'change_permissions': _(u'izmeneniye_dostupov'),
        'view_users_status_filter': _(u'prosmotr_filtra_po_statusam_polzovateley'),
        'change_user_status': _(u'izmeneniye_statusov_polzovateley'),

    },
    'courses': {
        'view_course': _(u'prosmotr_kursa'),
        'change_course_settings': _(u'izmenenie_nastroyek_kursa'),
    },
    'groups': {
        'view_gradebook': _(u'prosmotr_obshchey_vedomosti'),
        'create_task': _(u'sozdanie_zadachi'),
        'view_task_settings': _(u'prosmotr_nastroyek_zadach'),
        'change_task_title': _(u'izmeneniye_nazvaniya_zadachi'),
        'change_task_groups': _(u'izmeneniye_grupp_zadachi'),
        'change_task_is_hidden': _(u'izmeneniye_vidimosti_zadachi'),
        'change_task_parent_task': _(u'izmeneniye_roditelskoy_zadachi_v_zadache'),
        'change_task_task_text': _(u'izmeneniye_formulirovki_zadachi'),
        'change_task_score_max': _(u'izmeneniye_maksimalnogo_balla_zadach'),
        'change_task_contest': _(u'izmeneniye_nastroyek_kontesta_zadach'),
        'change_task_rb': _(u'izmeneniye_nastroyek_rb_zadach'),
        'change_task_type': _(u'izmeneniye_tipa_zadach'),
        'change_task_deadline_time': _(u'izmeneniye_daty_sdachi_zadach'),
        'change_task_one_file_upload': _(u'izmeneniye_otpravki_tolko_odnogo_fayla_zadach'),
    }
}


def get_perm_local_name(perm):
    return _get_perm_local_name(perm.content_type.app_label, perm.codename, perm.name)


def _get_perm_local_name(app_label, codename, name):
    local_group_name = ''

    if app_label in LOCALE_PERMS_APP_NAMES:
        local_group_name = LOCALE_PERMS_APP_NAMES[app_label]
        if codename in LOCALE_PERMS_NAMES[app_label]:
            local_perm_name = LOCALE_PERMS_NAMES[app_label][codename]
        else:
            local_perm_name = name
    else:
        local_perm_name = name

    return local_group_name, local_perm_name


def get_superuser_perms():
    perms = Permission.objects.none()
    for app_label in LOCALE_PERMS_NAMES.keys():
        perms |= Permission.objects.filter(
            content_type__app_label=app_label,
            codename__in=LOCALE_PERMS_NAMES[app_label].keys()
        ).distinct()

    return perms
