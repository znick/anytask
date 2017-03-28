# -*- coding: utf-8 -*-

from users.model_user_status import UserStatus

import logging

logger = logging.getLogger('django.request')


def get_statuses():
    statuses = {}
    for status in UserStatus.objects.all():
        status_info = {
            'id': status.id,
            'name': status.name,
        }
        if status.type in statuses:
            statuses[status.type]['values'].append(status_info)
        else:
            statuses[status.type] = {
                'type_name': status.get_type_display(),
                'values': [status_info],
            }
    return statuses