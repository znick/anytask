from django import template
from django.utils.translation import ugettext as _
from urlparse import urlparse

from groups.models import Group
from tasks.models import Task

register = template.Library()


@register.filter(name='get_path')
def get_path(url):
    return urlparse(url).path


@register.filter(name='get_title')
def get_title(url):
    if url.endswith('/'):
        url = url[:-1]
    if 'my_tasks' in url:
        return _('moi_zadachi')
    if 'queue' in url:
        return _('ochered_na_proverku')
    if 'group' in url and 'seminar' in url:
        url = url[url.rfind('seminar')+8:]
        id_seminar = url[:url.find('/')]
        seminar = Task.objects.get(id=id_seminar)
        id_group = url[url.rfind('group')+6:]
        group = Group.objects.get(id=id_group)
        return '%s: %s' % (seminar.title, group.name)
    if 'group' in url:
        id_ = url[url.rfind('/')+1:]
        group = Group.objects.get(id=id_)
        return group.name
    if 'seminar' in url:
        id_ = url[url.rfind('/') + 1:]
        seminar = Task.objects.get(id=id_)
        return seminar.title
    return _('obshaja_vedomost')
