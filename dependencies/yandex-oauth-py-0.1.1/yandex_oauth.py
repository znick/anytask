# ! /usr/bin/env python
# -*- coding: utf-8 -*-
import base64
import requests

"""
USAGE
>>> import yandex_oauth
# or from yandex_oauth import OAuthYandex
>>> oa = yandex_oauth.OAuthYandex(
'02c5296b18bc42****************',
'7eb579f49daf4a2***************')
>>> oa.get_code()
# just follow the url to get code for receiving token
'https://oauth.yandex.ru/authorize?response_type=code&client_id=02c5296b18bc42*************'
>>> oa.get_token(2338****)
{u'token_type': u'bearer',
u'access_token': u'a5f2e953058741******************',
u'expires_in': 31536000}

Copyright (c) 2015, Grudin wa_pis Anton.
License: MIT (see LICENSE for details)
"""

__author__ = 'Grudin Anton'
__version__ = '0.1.1'
__license__ = 'MIT'
VERSION = __version__


class OAuthYandex(object):
    client_id = None
    client_secret = None
    token = None
    code = None
    auth_url = None
    provider_url = "https://oauth.yandex.ru/authorize"
    oauth_url = "https://oauth.yandex.ru/token"

    def __init__(self, client_id, client_secret):
        """
        :client_id, client_secret - identical information for oauth app,
        you should register new app for ouauth,
        cat get it from https://oauth.yandex.ru/
        make request string to provider
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = self.provider_url + \
            "?response_type=code&client_id={0}" . format(client_id)

    def get_code(self):
        """
        return auth_url where you can get code for getting token
        :return: url
        """
        return self.auth_url

    def get_token(self, code):
        """
        code - you can get it from get_code
        :return: json obj
        """
        self.code = code
        headers = {}
        headers['Host'] = 'oauth.yandex.ru'
        headers['Content-type'] = 'application/x-www-form-urlencoded'
        headers['Authorization'] = self.get_basic_auth_token(
            self.client_id, self.client_secret)

        body = "grant_type=authorization_code&code={0}".format(self.code)
        headers['Content-Length'] = str(len(body))

        request = requests.request(
            "POST", self.oauth_url, data=body, headers=headers)
        return request.json()

    @staticmethod
    def get_basic_auth_token(path1, path2):
        """
        make Auth string for request.
        input pair login / password OR client_id / client_secret
        make string for basic https authorization join
        """
        token = "{0}:{1}".format(path1, path2).encode('utf-8')
        return "Basic {0}".format(base64.b64encode(token).decode('ascii'))
