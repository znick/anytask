from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext

from years.common import get_current_year
from cources.models import Cource

def index(request):
    
    current_year = get_current_year()
    cources = Cource.objects.filter(is_active=True).order_by('name')
    archive_cources = Cource.objects.exclude(is_active=True).order_by('year', 'name')
    
    context = {
        'current_year'  : current_year,
        'cources'       : cources,
        'archive_cources' : archive_cources,
    }
   
    return render_to_response('index.html', context, context_instance=RequestContext(request))
