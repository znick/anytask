# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.template.context import RequestContext


def blog_page(request):
    context = {}

    return render_to_response('blog.html', context, context_instance=RequestContext(request))
