from django.conf import settings
import requests


def api_request(method, endpoint, **kwargs):
    url = '{}{}'.format(settings.JUPYTER_NBGRADER_API_URL, endpoint)
    headers = kwargs.pop('headers', {})

    if hasattr(settings, 'JUPYTER_NBGRADER_AUTH_TOKEN'):
        headers['Authorization'] = 'Token {}'.format(settings.JUPYTER_NBGRADER_AUTH_TOKEN)

    return requests.request(method, url, headers=headers, **kwargs)


def get_or_create_assignment(name):
    r = api_request('put', '/assignments', json=dict(name=name))
    r.raise_for_status()
    return r.json()


def delete_assignment(name):
    r = api_request('delete', '/assignments/{}'.format(name))
    r.raise_for_status()
    return r.json()
