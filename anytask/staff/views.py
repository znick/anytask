# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.db.models import Q
from django.conf import settings
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML

from users.models import UserProfile, IssueFilterStudent, UserProfileFilter


def staff_page(request):
    user = request.user

    if not user.is_staff:
        return HttpResponseForbidden()

    user_profiles = UserProfile.objects.all()

    user_as_str = str(user.username) + '_userprofiles_filter'

    f = UserProfileFilter(request.GET, user_profiles)
    f.set()

    if f.form.data:
        request.session[user_as_str] = f.form.data
    elif user_as_str in request.session:
        f.form.data = request.session.get(user_as_str)

    f.form.helper = FormHelper(f.form)
    f.form.helper.form_method = 'get'
    f.form.helper.layout.append(HTML(u"""<div class="form-group row">
        <button id="button_filter" class="btn btn-secondary pull-xs-right" type="submit">Применить</button>
</div>"""))

    context = {
        'filter': f,
    }

    return render_to_response('staff.html', context, context_instance=RequestContext(request))