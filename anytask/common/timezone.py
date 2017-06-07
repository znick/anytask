# -*- coding: utf-8 -*-
import datetime
from pytz import timezone
from django.conf import settings


def convert_datetime(date_time, from_time_zone, to_time_zone=settings.TIME_ZONE):
    return timezone(from_time_zone).localize(date_time).\
        astimezone(timezone(to_time_zone)).replace(tzinfo=None)


def get_datetime_with_tz(value, geoid, user):
    value = datetime.datetime.strptime(value, '%d-%m-%Y %H:%M')
    tz = settings.DB.regionById(int(geoid)).as_dict['tzname'] if geoid else user.get_profile().time_zone
    return convert_datetime(value, tz)
