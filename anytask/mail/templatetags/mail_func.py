from django import template

register = template.Library()


@register.filter(name='get_html_url')
def get_html_url(name, url):
    return '<a href="{0}" target="_blank">{1}</a>'.format(url, name)
