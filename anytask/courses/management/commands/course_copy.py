from django.core.management.base import BaseCommand
from django.db import transaction

from courses.models import Course
from tasks.models import Task

import copy


class Command(BaseCommand):
    help = "Copy course"

    def add_arguments(self, parser):
        parser.add_argument('--course_id', dest='course_id', help='Course id', type=int)

    @transaction.atomic
    def handle(self, **options):
        course_id = options['course_id']
        if course_id:
            course_id = int(course_id)

        if not course_id:
            raise Exception("--course_id is required!")

        course_src = Course.objects.get(id=course_id)
        course_dst = Course()

        course_dst.__dict__ = copy.deepcopy(course_src.__dict__)
        course_dst.id = None
        course_dst.name += " copy"
        course_dst.save()

        for task_src in Task.objects.filter(course=course_src):
            if task_src.has_parent():
                continue

            print "Copy task {0}".format(task_src.title.encode("utf-8"))
            task_dst = Task()
            task_dst.__dict__ = copy.deepcopy(task_src.__dict__)
            task_dst.id = None
            task_dst.course = course_dst
            task_dst.save()

            for subtask_src in task_src.get_subtasks():
                print ">Copy subtask {0}".format(subtask_src.title.encode("utf-8"))
                subtask_dst = Task()

                subtask_dst.__dict__ = copy.deepcopy(subtask_src.__dict__)
                subtask_dst.id = None
                subtask_dst.parent_task = task_dst
                subtask_dst.course = course_dst
                subtask_dst.save()
