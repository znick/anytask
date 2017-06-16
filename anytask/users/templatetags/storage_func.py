from django import template
from django.utils.encoding import filepath_to_uri
from django.conf import settings

import urlparse

register = template.Library()


@register.filter(name='get_uri_media')
def get_uri(name):
    return urlparse.urljoin(settings.MEDIA_URL, filepath_to_uri(name))
