from bs4 import BeautifulSoup, Comment
from django import template

register = template.Library()

ALLOWED_TAGS = 'p i strong b u a h1 h2 h3 pre br img blockquote'
ALLOWED_TAGS_STRING = "Allowed tags: " + ALLOWED_TAGS


def sanitize_html(value):
    valid_tags = ALLOWED_TAGS.split()
    valid_attrs = 'href src target alt'.split()

    if not value:
        return ''

    soup = BeautifulSoup(value, features="html.parser")

    if not (soup.find('div', 'not-sanitize')):
        for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
            comment.extract()
        for tag in soup.findAll(True):
            if tag.name not in valid_tags:
                tag.hidden = True
            tag.attrs = [(attr, val) for attr, val in tag.attrs
                         if attr in valid_attrs]
        return '<p>' + soup.renderContents().decode('utf8').replace('javascript:', '').replace("\n", '</p><p>') + '</p>'
    return soup.renderContents().decode('utf8')


register.filter('sanitize', sanitize_html)
