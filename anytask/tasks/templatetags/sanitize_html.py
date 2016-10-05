from BeautifulSoup import BeautifulSoup, Comment
from django import template
from django.utils.translation import ugettext as _

import re

register = template.Library()

ALLOWED_TAGS = 'p i strong b u a h1 h2 h3 pre br img'
ALLOWED_TAGS_STRING = _("Allowed tags: ") + ALLOWED_TAGS

def sanitize_html(value):
    valid_tags = ALLOWED_TAGS.split()
    valid_attrs = 'href src'.split()

    if not value:
        return ''

    soup = BeautifulSoup(value)
    for comment in soup.findAll(
        text=lambda text: isinstance(text, Comment)):
        comment.extract()
    for tag in soup.findAll(True):
        if tag.name not in valid_tags:
            tag.hidden = True
        tag.attrs = [(attr, val) for attr, val in tag.attrs
                     if attr in valid_attrs]
    msg = ''
    msg_split = re.split(r'(<pre>(.*?)</pre>)',
                         soup.renderContents().decode('utf8').replace('javascript:', ''),
                         flags=re.I | re.M | re.S)
    i = 0
    while i in range(len(msg_split)):
        if msg_split[i].startswith('<pre>'):
            msg += msg_split[i]
            i += 1
        else:
            msg += msg_split[i].replace('\n', '<br/>')
        i += 1

    return msg
register.filter('sanitize', sanitize_html)
