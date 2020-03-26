# -*- coding: utf-8 -*-
import datetime
import requests
from pytz import timezone
from django.conf import settings


def get_tz(geoid):
    if settings.USE_LOCAL_GEOBASE:
        return settings.DB.regionById(int(geoid)).as_dict['tzname']

    try:
        return requests.get(settings.GEOBASE_API,
                            params={'id': geoid},
                            headers={"Authorization": "anytask"}
                            ).json()['tzname']
    except:  # noqa
        return settings.TIME_ZONE


def convert_datetime(date_time, from_time_zone, to_time_zone=settings.TIME_ZONE):
    return timezone(from_time_zone).localize(date_time.replace(tzinfo=None)).\
        astimezone(timezone(to_time_zone))


def get_datetime_with_tz(value, geoid, user):
    value = datetime.datetime.strptime(value, '%d-%m-%Y %H:%M')
    if geoid:
        tz = get_tz(geoid)
    else:
        tz = user.profile.time_zone or settings.TIME_ZONE
    return convert_datetime(value, tz)
