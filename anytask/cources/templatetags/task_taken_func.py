from BeautifulSoup import BeautifulSoup, Comment
from django import template
from django.utils.translation import ugettext as _


register = template.Library()

@register.filter(name='score')
def task_taken_score(d, task):
    if d.has_key(task.id):
    	return d[task.id].score
    return 0

@register.filter(name='comment')
def task_taken_comment(d, task):
	if d.has_key(task.id):
		return d[task.id].teacher_comments
	return ''
	
