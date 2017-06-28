# -*- coding: utf-8 -*-
import datetime
import requests
from pytz import timezone
from django.conf import settings


def convert_datetime(date_time, from_time_zone, to_time_zone=settings.TIME_ZONE):
    return timezone(from_time_zone).localize(date_time.replace(tzinfo=None)).\
        astimezone(timezone(to_time_zone)).replace(tzinfo=None)


def get_datetime_with_tz(value, geoid, user):
    value = datetime.datetime.strptime(value, '%d-%m-%Y %H:%M')
    if geoid:
        tz = requests.get(settings.GEOBASE_API,
                          params={'id': geoid},
                          headers={"Authorization": "anytask"}
                          ).json()['tzname']
    else:
        tz = user.get_profile().time_zone
    return convert_datetime(value, tz)
