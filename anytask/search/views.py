# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from haystack.query import SearchQuerySet


from users.models import UserProfile
from courses.models import Course
from schools.models import School
import json


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
    return render_to_response('search.html', context, context_instance=RequestContext(request))


@login_required()
def ajax_search_users(request):
    if 'q' not in request.GET:
        return HttpResponseForbidden()

    max_result = 3
    result, _ = search_users(request.GET.get('q', ''), request.user, max_result + 1)

    return HttpResponse(json.dumps({'result': result[:max_result],
                                    'is_limited': True if len(result) > max_result else False}),
                        content_type='application/json')


@login_required()
def ajax_search_courses(request):
    if 'q' not in request.GET:
        return HttpResponseForbidden()

    max_result = 3

    result, _ = search_courses(request.GET.get('q', ''), request.user, max_result + 1)

    return HttpResponse(json.dumps({'result': result[:max_result],
                                    'is_limited': True if len(result) > max_result else False}),
                        content_type='application/json')


def search_users(query, user, max_result=None):
    result = []
    result_objs = []

    if query:
        user_is_staff = user.is_staff
        user_is_teacher = None
        if not user_is_staff:
            user_is_teacher = True if Course.objects.filter(teachers=user).count() else False

        sgs = SearchQuerySet().models(UserProfile).exclude(user_id=user.id)

        sgs_fullname = sgs.autocomplete(fullname_auto=query)

        sgs_login = sgs.autocomplete(login_auto=query)

        if user_is_staff or user_is_teacher:
            sgs_ya_contest_login = sgs.autocomplete(ya_contest_login_auto=query)
            sgs_ya_passport_email = sgs.autocomplete(ya_passport_email_auto=query)
        else:
            sgs_ya_contest_login = sgs.none()
            sgs_ya_passport_email = sgs.none()

        sgs = sgs_fullname | sgs_login | sgs_ya_contest_login | sgs_ya_passport_email

        if not user_is_staff:
            groups = user.group_set.all()
            courses = Course.objects.filter(groups__in=groups)
            schools = School.objects.filter(courses__in=courses)
            courses_teacher = Course.objects.filter(teachers=user)
            schools_teacher = School.objects.filter(courses__in=courses_teacher)

            for sg in sgs:
                user_to_show = sg.object.user
                groups_user_to_show = user_to_show.group_set.all()
                courses_user_to_show = Course.objects.filter(groups__in=groups_user_to_show)
                schools_user_to_show = School.objects.filter(courses__in=courses_user_to_show)
                courses_user_to_show_teacher = Course.objects.filter(teachers=user_to_show)
                schools_user_to_show_teacher = School.objects.filter(courses__in=courses_user_to_show_teacher)

                user_school_user_to_show = False
                if (schools_user_to_show | schools_user_to_show_teacher) & (schools | schools_teacher):
                    user_school_user_to_show = True

                if not user_school_user_to_show:
                    continue
                user_to_show_teach_user = False
                if courses_user_to_show_teacher & courses:
                    user_to_show_teach_user = True

                user_teach_user_to_show = False
                if courses_teacher & courses_user_to_show:
                    user_teach_user_to_show = True

                show_email = user_to_show.get_profile().show_email or \
                             user_teach_user_to_show or \
                             user_to_show_teach_user

                result.append([user_to_show.get_full_name(),
                               user_to_show.username,
                               sg.object.ya_contest_login if user_is_teacher else '',
                               user_to_show.get_absolute_url(),
                               sg.object.avatar.url if sg.object.avatar else '',
                               user_to_show.email if show_email else '',
                               user_to_show.ya_passport_email if show_email else ''])
                result_objs.append(sg.object)

                if len(result) == max_result:
                    break

        else:
            for sg in sgs[:max_result]:
                result.append([sg.object.user.get_full_name(),
                               sg.object.user.username,
                               sg.object.ya_contest_login,
                               sg.object.user.get_absolute_url(),
                               sg.object.avatar.url if sg.object.avatar else '',
                               sg.object.user.email,
                               sg.object.ya_passport_email])
                result_objs.append(sg.object)

    return result, result_objs


def search_courses(query, user, max_result=None):
    result = []
    result_objs = []

    if query:
        user_is_staff = user.is_staff
        sgs_name = SearchQuerySet().models(Course).order_by('-is_active')

        if not user_is_staff:
            groups = user.group_set.all()
            courses_ids = (Course.objects.filter(groups__in=groups) | Course.objects.filter(teachers=user)) \
                .values_list('id', flat=True)

            sgs_name = sgs_name.filter(course_id__in=courses_ids).autocomplete(name_auto=query)
        else:
            sgs_name = sgs_name.autocomplete(name_auto=query)

        for sg in sgs_name[:max_result]:
            result.append([unicode(sg.object.name),
                           unicode(sg.object.year),
                           sg.object.get_absolute_url(),
                           [sch.name for sch in sg.object.school_set.all()],
                           sg.object.is_active])
            result_objs.append(sg.object)

    return result, result_objs
