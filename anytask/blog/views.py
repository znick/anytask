# -*- coding: utf-8 -*-

from django.shortcuts import render


def blog_page(request):
    context = {}

    return render(request, 'blog.html', context)
