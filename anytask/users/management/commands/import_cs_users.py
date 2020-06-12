"""
A management command which deletes expired accounts (e.g.,
accounts which signed up but never activated) from the database.

Calls ``RegistrationProfile.objects.delete_expired_users()``, which
contains the actual logic for determining which accounts are deleted.

"""

from django.core.management.base import BaseCommand as NoArgsCommand
from django.contrib.auth.models import User

from xml.etree.ElementTree import parse
import sys
import random
import string


def get_users_from_cs_xml(cs_xml_fn):
    doc = parse(cs_xml_fn)
    for student_el in doc.getElementsByTagName("student"):
        student = {
            'username': student_el.getAttribute('dir'),
            'name': student_el.getAttribute('name'),
            'email': student_el.getAttribute('email'),
            'year': student_el.getAttribute('year'),
        }
        yield student


class Command(NoArgsCommand):
    help = "Import users from cs.usu.edu.ru/home. Put default.xml to STDIN"

    def handle_noargs(self, **options):
        for student in get_users_from_cs_xml(sys.stdin):
            last_name, first_name = student['name'].split(' ', 1)
            username = student['username']
            email = student['email']

            user, created = User.objects.get_or_create(username=username, first_name=first_name, last_name=last_name,
                                                       email=email)

            if (user.password == "") or (user.has_usable_password() is False):
                user.set_password(''.join(random.choice(string.letters) for i in range(20)))
                user.save()

            print("{0} {1}".format(user, user.get_full_name().encode("utf-8")))
