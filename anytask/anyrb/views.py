# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from issues.models import Issue


@csrf_exempt
def message_from_rb(request, review_id):
    for one_issue in Issue.objects.filter(task__rb_integrated=True).order_by('-update_time'):
        try:
            if one_issue.get_byname('review_id') == review_id:
                issue = one_issue
                break
        except:
            pass

    if request.method == 'POST':
        value = {'files': [], 'comment': ''}
        value['comment'] = u'<p><strong>{2} <a href="{1}/r/{0}">Review request {0}</a></strong>.</p>' \
            .format(review_id, settings.RB_API_URL, _(u'novyj_kommentarij'))
        author = get_object_or_404(User, username=request.POST.get('author', ''))
        issue.set_byname('comment', value, author)
        issue.save()
        return HttpResponse(status=201)
