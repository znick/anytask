from django.shortcuts import render
from schools.models import School


def index(request):
    schools = School.objects.all().order_by('name')

    # current_year = get_current_year()
    # courses = Course.objects.filter(is_active=True).order_by('name')
    # archive_courses = Course.objects.exclude(is_active=True).order_by('year', 'name')

    context = {
        'schools': schools,
    }

    return render(request, 'index.html', context)
