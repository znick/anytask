from django.shortcuts import render_to_response, get_object_or_404, redirect
from tasks.models import Task
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from tasks.models import TaskTaken
import settings

import json

def get_task_text_popup(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    context = {
        'task' : task,
    }
    
    return render_to_response('task_text_popup.html', context, context_instance=RequestContext(request))


def update_status_check(request, redirect=True):
    if request.method == "POST":
        try:
            student_id = int(request.POST['student_id'])
            task_id = int(request.POST['task_id'])
            task = Task.objects.get(id=task_id)
            student = User.objects.get(id=student_id)
            task_taken, created = TaskTaken.objects.get_or_create(user=student, task=task)
            new_status = request.POST['new_status']
            if task_taken.user_can_change_status(request.user, new_status):
                task_taken.status_check = new_status
                task_taken.save()
        except ObjectDoesNotExist:
            pass
        if redirect:
            return HttpResponseRedirect(reverse('courses.views.tasks_list', kwargs={'course_id':task_taken.task.course.id}))
    else:
        return HttpResponseForbidden()


def ajax_get_review_data(request, task_id, student_id):
    if not request.is_ajax():
        return HttpResponseForbidden()
    
    id_issue_gr_review = ""
    pdf_link = ""
    gr_review_update_time = ""
    pdf_update_time = ""

    try:
        task = Task.objects.get(id=task_id)
        student = User.objects.get(id=student_id)
        task_taken, created = TaskTaken.objects.get_or_create(user=student, task=task)
        
        if task_taken.id_issue_gr_review:
            id_issue_gr_review = task_taken.id_issue_gr_review
            gr_review_update_time = task_taken.gr_review_update_time.strftime('%d/%m/%Y %H:%M')
        
        if task_taken.pdf:
            pdf_link = task_taken.pdf.url
            pdf_update_time = task_taken.pdf_update_time.strftime('%d/%m/%Y %H:%M')
        
    except ObjectDoesNotExist:
        pass
    
    review_data = {
            'id_issue_gr_review' : id_issue_gr_review,
            'pdf_link' : pdf_link,
            'gr_review_update_time' : gr_review_update_time,
            'pdf_update_time' : pdf_update_time,
        }
    return HttpResponse(json.dumps(review_data), content_type="application/json")   

def ajax_predict_status(request, task_id, student_id, score):
    if not request.is_ajax():
        return HttpResponseForbidden()

    predicted_status = ""
    
    try:
        score = float(score) 
        task = Task.objects.get(id=task_id)
        student = User.objects.get(id=student_id)

        task_taken, created = TaskTaken.objects.get_or_create(user=student, task=task)
        
        eps = 10**(-5)
        if abs(score - task.score_max) < eps:
            predicted_status = TaskTaken.OK
        elif abs(score - task_taken.score) > eps:
            predicted_status = TaskTaken.EDIT
        else:
            predicted_status = task_taken.status_check

    except ObjectDoesNotExist:
        pass

    data = {
            'predicted_status' : predicted_status,
        }

    return HttpResponse(json.dumps(data), content_type="application/json")

def ajax_get_status_check(request, task_id, student_id):
    if not request.is_ajax():
        return HttpResponseForbidden()
    
    current_status = ""
    choices_status = []
    is_possible_status = []
    
    try:    
        task = Task.objects.get(id=task_id)
        student = User.objects.get(id=student_id)

        task_taken, created = TaskTaken.objects.get_or_create(user=student, task=task)
        choices_status = TaskTaken.STATUS_CHECK_CHOICES
        is_possible_status = [task_taken.user_can_change_status(request.user, status[0]) for status in choices_status]

        current_status = task_taken.status_check
        
        for status in choices_status:
            if status[0] == current_status:
                current_status = status
                break

        is_possible_status = is_possible_status
        
    except ObjectDoesNotExist:
        pass
    
    status_check_data = {
            'current_status' : current_status,
            'choices_status' : choices_status,
            'is_possible_status' : is_possible_status,
        }

    return HttpResponse(json.dumps(status_check_data), content_type="application/json")


def ajax_get_teacher(request, task_id, student_id):
    if not request.is_ajax():
        return HttpResponseForbidden()

    teacher_name = ""
    try:
        task = Task.objects.get(id=task_id)
        student = User.objects.get(id=student_id)
        task_taken, created = TaskTaken.objects.get_or_create(user=student, task=task)
        if task_taken.teacher:
            teacher_name = task_taken.teacher.get_full_name()
    except ObjectDoesNotExist:
        pass

    data = {
        'teacher_name' : teacher_name
    }

    return HttpResponse(json.dumps(data), content_type="application/json")


def ajax_set_teacher(request, task_id, student_id, teacher_id):
    if not request.is_ajax():
        return HttpResponseForbidden()
    
    try:
        task = Task.objects.get(id=task_id)
        student = User.objects.get(id=student_id)
        teacher = User.objects.get(id=teacher_id)
        task_taken, created = TaskTaken.objects.get_or_create(user=student, task=task)
        if (task_taken.user_can_change_teacher(request.user)):
            task_taken.teacher = teacher
            task_taken.save()
    except ObjectDoesNotExist:
        pass

    return HttpResponse({}, content_type="application/json")


def ajax_delete_teacher(request, task_id, student_id):
    if not request.is_ajax():
        return HttpResponseForbidden()
    
    try:
        task = Task.objects.get(id=task_id)
        student = User.objects.get(id=student_id)
        task_taken, created = TaskTaken.objects.get_or_create(user=student, task=task)
        if task_taken.user_can_change_teacher(request.user):
            task_taken.teacher = None
            task_taken.save()
    except ObjectDoesNotExist:
        pass

    return HttpResponse({}, content_type="application/json")
