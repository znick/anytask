from django.core.management.base import BaseCommand
from django.db import transaction

from groups.models import Group

from optparse import make_option
import copy


class Command(BaseCommand):
    help = "Copy group"

    option_list = BaseCommand.option_list + (
        make_option('--group_id',
                    action='store',
                    dest='group_id',
                    default=None,
                    help='Group id'),
    )

    @transaction.commit_on_success
    def handle(self, **options):
        group_id = options['group_id']
        if group_id:
            group_id = int(group_id)

        if not group_id:
            raise Exception("--group_id is required!")

        group_src = Group.objects.get(id=group_id)
        group_dst = Group()

        group_dst.__dict__ = copy.deepcopy(group_src.__dict__)
        group_dst.id = None
        group_dst.name += " copy"
        group_dst.save()

        for student_src in group_src.students.all():
            print("Copy student {0}".format(student_src.get_full_name().encode("utf-8")))
            group_dst.students.add(student_src)
