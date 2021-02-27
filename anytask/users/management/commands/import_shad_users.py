from django.core.management.base import BaseCommand as NoArgsCommand
from django.contrib.auth.models import User
from groups.models import Group
from django.contrib.auth.forms import PasswordResetForm

import sys


class Command(NoArgsCommand):
    help = "Import user from text file"

    def handle_noargs(self, **options):
        # user = User.objects.get(pk=1)
        group = Group.objects.get(pk=2)
        # group.students.add(user)
        for student in sys.stdin:
            fields = student.strip().split(' ')
            email = fields[0]
            # print email, len(fields)
            if len(fields) > 3:
                continue

            username = email.split('@')[0]
            last_name = fields[1]
            first_name = fields[2]
            print(email, username, last_name, first_name)

            user, created = User.objects.get_or_create(username=username, first_name=first_name, last_name=last_name,
                                                       email=email)

            group.students.add(user)
            reset_form = PasswordResetForm({'email': email})
            print(reset_form)
            reset_form.save()

        group.save()
