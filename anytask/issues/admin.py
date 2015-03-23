from issues.model_issue_field import IssueField
from issues.models import Issue, Event
from django.contrib import admin

admin.site.register(Issue)
admin.site.register(Event)
admin.site.register(IssueField)