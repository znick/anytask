# -*- coding: utf-8 -*-

import json

from django.core.exceptions import ValidationError

LANG_DEFAULT = 'ru'


def validate_json(value):
    try:
        json_name = json.loads(value)
        if LANG_DEFAULT not in json_name:
            raise KeyError
    except ValueError:
        raise ValidationError(u'%s is not a json string' % value)
    except KeyError:
        raise ValidationError(u'%s does not contains required "ru" key' % value)


def get_value_from_json(json_value, lang=LANG_DEFAULT):
    try:
        dict_value = json.loads(json_value)
        if lang in dict_value:
            value = dict_value[lang]
        else:
            value = dict_value[LANG_DEFAULT]
    except ValueError:
        value = json_value

    return u'{0}'.format(value)
