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

    if 'max' in request.GET:
        max_result = int(request.GET["max"])
    else:
        max_result = 3

    result, _ = search_users(request.GET.get('q', ''), request.user, max_result + 1)

    return HttpResponse(json.dumps({'result': result[:max_result],
                                    'is_limited': True if len(result) > max_result else False}),
                        content_type='application/json')


@login_required()
def ajax_search_courses(request):
    if 'q' not in request.GET:
        return HttpResponseForbidden()

    if 'max' in request.GET:
        max_result = int(request.GET["max"])
    else:
        max_result = 3

    result, _ = search_courses(request.GET.get('q', ''), request.user, max_result + 1)

    return HttpResponse(json.dumps({'result': result[:max_result],
                                    'is_limited': True if len(result) > max_result else False}),
                        content_type='application/json')


def search_users(query, user, max_result=None):
    result = []
    result_objs = []

    if not query:
        return result, result_objs

    user_is_staff = user.is_staff
    user_is_teacher = None
    if not user_is_staff:
        user_is_teacher = True if Course.objects.filter(teachers=user).count() else False

    name_q = (
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(user__username__icontains=query)
    )

    if user_is_staff or user_is_teacher:
        name_q |= (
            Q(ya_contest_login__icontains=query) |
            Q(ya_passport_email__icontains=query) |
            Q(user__email__icontains=query)
        )

    profiles = (
        UserProfile.objects
        .filter(name_q)
        .exclude(user=user)
        .select_related('user')
        .prefetch_related('user_status')
    )

    if not user_is_staff:
        groups = user.group_set.all()
        courses = Course.objects.filter(groups__in=groups)
        schools = School.objects.filter(courses__in=courses)
        courses_teacher = Course.objects.filter(teachers=user)
        schools_teacher = School.objects.filter(courses__in=courses_teacher)

        for profile in profiles:
            user_to_show = profile.user
            groups_user_to_show = user_to_show.group_set.all()
            courses_user_to_show = Course.objects.filter(groups__in=groups_user_to_show)
            schools_user_to_show = School.objects.filter(courses__in=courses_user_to_show)
            courses_user_to_show_teacher = Course.objects.filter(teachers=user_to_show)
            schools_user_to_show_teacher = School.objects.filter(courses__in=courses_user_to_show_teacher)

            if not (schools_user_to_show | schools_user_to_show_teacher) & (schools | schools_teacher):
                continue

            user_to_show_teach_user = bool(courses_user_to_show_teacher & courses)
            user_teach_user_to_show = bool(courses_teacher & courses_user_to_show)

            show_email = profile.show_email or user_teach_user_to_show or user_to_show_teach_user

            result.append({
                "fullname": user_to_show.get_full_name(),
                "username": user_to_show.username,
                "ya_contest_login": profile.ya_contest_login if user_is_teacher else '',
                "url": user_to_show.get_absolute_url(),
                "avatar": profile.avatar.url if profile.avatar else '',
                "email": user_to_show.email if show_email else '',
                "ya_passport_email": profile.ya_passport_email if show_email else '',
                "id": user_to_show.id,
                "statuses": list(profile.user_status.values_list('name', 'color'))
            })
            result_objs.append(profile)

            if max_result and len(result) == max_result:
                break
    else:
        qs = profiles[:max_result] if max_result else profiles
        for profile in qs:
            result.append({
                "fullname": profile.user.get_full_name(),
                "username": profile.user.username,
                "ya_contest_login": profile.ya_contest_login,
                "url": profile.user.get_absolute_url(),
                "avatar": profile.avatar.url if profile.avatar else '',
                "email": profile.user.email,
                "ya_passport_email": profile.ya_passport_email,
                "id": profile.user.id,
                "statuses": list(profile.user_status.values_list('name', 'color'))
            })
            result_objs.append(profile)

    return result, result_objs


def search_courses(query, user, max_result=None):
    result = []
    result_objs = []

    if not query:
        return result, result_objs

    user_is_staff = user.is_staff

    courses_qs = Course.objects.filter(name__icontains=query).order_by('-is_active')

    if not user_is_staff:
        groups = user.group_set.all()
        allowed_ids = (
            Course.objects.filter(groups__in=groups) | Course.objects.filter(teachers=user)
        ).values_list('id', flat=True)
        courses_qs = courses_qs.filter(id__in=allowed_ids)

    if max_result:
        courses_qs = courses_qs[:max_result]

    for course in courses_qs:
        result.append({
            'name': str(course.name),
            'year': str(course.year),
            'url': course.get_absolute_url(),
            'schools': [sch.name for sch in course.school_set.all()],
            'is_active': course.is_active
        })
        result_objs.append(course)

    return result, result_objs
