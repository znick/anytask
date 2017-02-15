# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Count
from anytask.courses.models import StudentCourseMark, Course


class Command(BaseCommand):
    help = "Find mark duplicates in StudentCourseMark"

    def handle(self, *args, **options):
        unique_fields = ['student', 'course']
        duplicates = (StudentCourseMark.objects.values(*unique_fields).order_by()
                      .annotate(count_id=Count('id')).filter(count_id__gt=1))

        if duplicates:
            with open('mark_duplicates', 'w') as f:
                for item in duplicates:
                    row = u'course {0}\t\tstudent {1}\t\tmarks_count {2}'\
                        .format(Course.objects.get(pk=item['course']).name,
                                User.objects.get(pk=item['student']).username,
                                item['count_id'])
                    f.write(row.encode('utf8'))
        else:
            print 'No duplicates'


