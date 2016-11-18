# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext


def blog_page(request):
    context = {}

    return render_to_response('blog.html', context, context_instance=RequestContext(request))
