from django import template
from issues.model_issue_status import IssueStatus


register = template.Library()


@register.filter(name='label_color')
def issue_label_color(status_id):
    try:
        return IssueStatus.objects.get(id=int(status_id)).color
    except:
        pass
    return IssueStatus.COLOR_DEFAULT
