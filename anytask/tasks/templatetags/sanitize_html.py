from BeautifulSoup import BeautifulSoup, Comment
from django import template
from django.utils.translation import ugettext as _


register = template.Library()

ALLOWED_TAGS = 'p i strong b u a h1 h2 h3 pre br img'
ALLOWED_TAGS_STRING = _("Allowed tags: ") + ALLOWED_TAGS

def sanitize_html(value):
    valid_tags = ALLOWED_TAGS.split()
    valid_attrs = 'href src target'.split()

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
    return soup.renderContents().decode('utf8').replace('javascript:', '').replace("\n",'<br/>')

register.filter('sanitize', sanitize_html)
