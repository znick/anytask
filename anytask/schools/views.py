# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from schools.models import School


@login_required
def school_page(request, school_link):
    school = get_object_or_404(School, link=school_link)
    courses = school.courses.all().filter(is_active=True).order_by('name')

    context = {
        'school': school,
        'courses': courses,
    }

    return render(request, 'school_page.html', context)


@login_required
def archive_page(request, school_link):
    school = get_object_or_404(School, link=school_link)
    courses = school.courses.all().filter(is_active=False).order_by('name')

    context = {
        'school': school,
        'courses': courses,
    }

    return render(request, 'archive_page.html', context)
