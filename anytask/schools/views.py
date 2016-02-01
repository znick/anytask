# Create your views here.
@login_required
def school_page(request, school_id):
    school = get_object_or_404(School, id=school_id)
    courses = school.courses

    context = {
        'courses' : courses,
    }
   
    return render_to_response('school_page.html', context, context_instance=RequestContext(request))