# -*- coding: utf-8 -*-

from . import plugin_manager


def plugins(request):
    return {'plugins': plugin_manager.get_req_data(request)}
