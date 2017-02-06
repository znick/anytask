# -*- coding: utf-8 -*-

from issues.model_issue_field import IssueField
from issues.model_issue_status import IssueStatus, IssueStatusSystem
from issues.models import Issue, Event
from django.contrib import admin
from django.utils.translation import ugettext as _


def display_color(obj):
    return u'<span style="' \
           u'padding: .25em .4em;' \
           u'font-size: 75%;' \
           u'font-weight: 700;' \
           u'line-height: 1;' \
           u'color: #fff;' \
           u'text-align: center;' \
           u'white-space: nowrap;' \
           u'vertical-align: baseline;' \
           u'border-radius: .25rem;' \
           u'background-color:{0}' \
           u'">{1}</span>'.format(obj.color, obj.name)
display_color.short_description = _(u'Статус')
display_color.allow_tags = True


class IssueAdmin(admin.ModelAdmin):
    exclude = ('status',)


class IssueStatusAdmin(admin.ModelAdmin):
    list_display = (display_color, 'tag')
    exclude = ('hidden',)
    search_fields = ('name',)

    def queryset(self, request):
        qs = super(IssueStatusAdmin, self).queryset(request)
        # if request.user.is_superuser:
        #     return qs
        return qs.exclude(hidden=True)


class IssueStatusSystemAdmin(admin.ModelAdmin):
    list_display = ('name', )
    filter_horizontal = ('statuses',)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "statuses":
            kwargs["queryset"] = IssueStatus.objects.exclude(hidden=True)
        return super(IssueStatusSystemAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)


admin.site.register(Issue)
admin.site.register(Event)
admin.site.register(IssueField)
admin.site.register(IssueStatus, IssueStatusAdmin)
admin.site.register(IssueStatusSystem, IssueStatusSystemAdmin)
