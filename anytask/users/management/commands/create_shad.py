"""
A management command which deletes expired accounts (e.g.,
accounts which signed up but never activated) from the database.

Calls ``RegistrationProfile.objects.delete_expired_users()``, which
contains the actual logic for determining which accounts are deleted.

"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from groups.models import Group
from courses.models import Course
from schools.models import School
from years.common import get_or_create_current_year
from years.models import Year

from xml.etree.ElementTree import parse
from optparse import make_option
import sys
import random
import string


def get_users_from_cs_xml(cs_xml_fn):
    doc = parse(cs_xml_fn)
    for student_el in doc.getElementsByTagName("student"):
        student = {
            'login': student_el.getAttribute('login'),
            'name': student_el.getAttribute('name'),
            'grp': student_el.getAttribute('grp'),
        }
        yield student


class Command(BaseCommand):
    help = "Creating shad users, python course, shad school."

    option_list = BaseCommand.option_list + (
        make_option('--year',
                    action='store',
                    dest='year',
                    default=None,
                    help='Course start year'),
    )

    def handle(self, **options):
        year = options['year']
        if year:
            year = int(year)
            year, _ = Year.objects.get_or_create(start_year=year)

        if not year:
            year = get_or_create_current_year()

        school, created = School.objects.get_or_create(link='shad', name='School of Data Analysis')
        if created:
            print("WARNING: NEW School created!")
            school.save()

        course, created = Course.objects.get_or_create(year=year, name='Python')
        if created:
            print("WARNING: NEW Course created!")
            course.is_active = True
            course.contest_integrated = True
            course.save()

        school.courses.add(course)

        for student in get_users_from_cs_xml(sys.stdin):
            last_name, first_name = student['name'].split(' ', 1)
            username = student['login']
            group_name = student['grp']

            try:
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                print("Creating new user! : {0}".format(username.encode("utf-8")))
                user = User.objects.create(username=username)
                user.last_name = last_name
                user.first_name = first_name

            if (user.password == "") or (not user.has_usable_password()):
                user.set_password(''.join(random.choice(string.letters) for i in range(20)))
                user.save()

            group, _ = Group.objects.get_or_create(year=year, name=group_name)
            course.groups.add(group)
            group.students.add(user)
            print("{0} {1} {2}".format(user, user.get_full_name().encode("utf-8"), group))
