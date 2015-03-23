from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext

from years.common import get_current_year
from courses.models import Course

def index(request):
    
    current_year = get_current_year()
    courses = Course.objects.filter(is_active=True).order_by('name')
    archive_courses = Course.objects.exclude(is_active=True).order_by('year', 'name')
    
    context = {
        'current_year'  : current_year,
        'courses'       : courses,
        'archive_courses' : archive_courses,
    }
   
    return render_to_response('index.html', context, context_instance=RequestContext(request))
