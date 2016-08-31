from django import template
from issues.model_issue_field import IssueStatusField


register = template.Library()


@register.filter(name='label_color')
def issue_label_color(status_id):
    try:
        return IssueStatusField.objects.get(id=int(status_id)).color
    except:
        pass
    return IssueStatusField.COLOR_DEFAULT
