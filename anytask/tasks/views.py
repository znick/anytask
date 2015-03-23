from django.shortcuts import render_to_response, get_object_or_404, redirect
from tasks.models import Task
from django.template import RequestContext

def get_task_text_popup(request, task_id):
    task = get_object_or_404(Task, id = task_id)
    
    context = {
        'task' : task,
    }
    
    return render_to_response('task_text_popup.html', context, context_instance=RequestContext(request))
