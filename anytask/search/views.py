# -*- coding: utf-8 -*-

import json

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render

from courses.models import Course
from schools.models import School
from users.models import UserProfile


@login_required()
def search_page(request):
    user = request.user
    query = request.GET.get('q', '')

    context = {
        'user': request.user,
        'user_is_teacher': True if Course.objects.filter(teachers=user).count() else False,
        'query': query,
        'user_profiles': search_users(query, user)[1],
        'courses': search_courses(query, user)[1],
    }
    return render(request, 'search.html', context)


@login_required()
def ajax_search_users(request):
    if 'q' not in request.GET:
        return HttpResponseForbidden()

    max_result = int(request.GET.get('max', 3))
    result, _ = search_users(request.GET.get('q', ''), request.user, max_result + 1)

    return HttpResponse(json.dumps({'result': result[:max_result],
                                    'is_limited': len(result) > max_result}),
                        content_type='application/json')


@login_required()
def ajax_search_courses(request):
    if 'q' not in request.GET:
        return HttpResponseForbidden()

    max_result = int(request.GET.get('max', 3))
    result, _ = search_courses(request.GET.get('q', ''), request.user, max_result + 1)

    return HttpResponse(json.dumps({'result': result[:max_result],
                                    'is_limited': len(result) > max_result}),
                        content_type='application/json')


def _build_user_search_query(query, extra_fields=False):
    q = Q()
    for word in query.split():
        word_q = (
            Q(user__first_name__icontains=word)
            | Q(user__last_name__icontains=word)
            | Q(user__username__icontains=word)
        )
        if extra_fields:
            word_q |= (
                Q(ya_contest_login__icontains=word)
                | Q(ya_passport_email__icontains=word)
                | Q(user__email__icontains=word)
            )
        q &= word_q
    return q


def _profile_to_dict(profile, show_email=True, show_ya_contest=True):
    return {
        "fullname": profile.user.get_full_name(),
        "username": profile.user.username,
        "ya_contest_login": profile.ya_contest_login if show_ya_contest else '',
        "url": profile.user.get_absolute_url(),
        "avatar": profile.avatar.url if profile.avatar else '',
        "email": profile.user.email if show_email else '',
        "ya_passport_email": profile.ya_passport_email if show_email else '',
        "id": profile.user.id,
        "statuses": list(profile.user_status.values_list('name', 'color')),
    }


def search_users(query, user, max_result=None):
    if not query:
        return [], []

    user_is_staff = user.is_staff
    user_is_teacher = not user_is_staff and Course.objects.filter(teachers=user).exists()

    profiles = (
        UserProfile.objects
        .filter(_build_user_search_query(query, extra_fields=user_is_staff or user_is_teacher))
        .exclude(user=user)
        .select_related('user')
        .prefetch_related('user_status')
    )

    if user_is_staff:
        qs = profiles[:max_result] if max_result else profiles
        result_objs = list(qs)
        result = [_profile_to_dict(p) for p in result_objs]
        return result, result_objs

    groups = user.group_set.all()
    courses = Course.objects.filter(groups__in=groups)
    schools = School.objects.filter(courses__in=courses)
    courses_teacher = Course.objects.filter(teachers=user)
    schools_teacher = School.objects.filter(courses__in=courses_teacher)
    searcher_schools = schools | schools_teacher

    result = []
    result_objs = []
    for profile in profiles:
        u = profile.user
        target_courses = Course.objects.filter(groups__in=u.group_set.all())
        target_schools = School.objects.filter(courses__in=target_courses)
        target_courses_teacher = Course.objects.filter(teachers=u)
        target_schools_teacher = School.objects.filter(courses__in=target_courses_teacher)

        if not (target_schools | target_schools_teacher) & searcher_schools:
            continue

        show_email = (
            profile.show_email
            or bool(target_courses_teacher & courses)
            or bool(courses_teacher & target_courses)
        )

        result.append(_profile_to_dict(profile, show_email=show_email, show_ya_contest=user_is_teacher))
        result_objs.append(profile)

        if max_result and len(result) == max_result:
            break

    return result, result_objs


def search_courses(query, user, max_result=None):
    if not query:
        return [], []

    courses_qs = Course.objects.filter(name__icontains=query).order_by('-is_active')

    if not user.is_staff:
        groups = user.group_set.all()
        allowed_ids = (
            Course.objects.filter(groups__in=groups) | Course.objects.filter(teachers=user)
        ).values_list('id', flat=True)
        courses_qs = courses_qs.filter(id__in=allowed_ids)

    if max_result:
        courses_qs = courses_qs[:max_result]

    result = []
    result_objs = []
    for c in courses_qs:
        result.append({
            'name': str(c.name),
            'year': str(c.year),
            'url': c.get_absolute_url(),
            'schools': [sch.name for sch in c.school_set.all()],
            'is_active': c.is_active,
        })
        result_objs.append(c)

    return result, result_objs
