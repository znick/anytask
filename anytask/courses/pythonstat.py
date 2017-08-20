from django.db.models import Q
from tasks.models import TaskTaken


class PythonTaskStat(object):
    def __init__(self, course_tasks):
        self.tasks = course_tasks
        self.group_stat = {}
        self.course_stat = {
            'total': 0.0,
            'active_students': 0,
            'avg_score': 0.0,
        }

    def update(self, group):
        self._group_update(group)
        self._course_update(group)

    def get_group_stat(self):
        return [(group, stat['student_stat']) for (group, stat) in self.group_stat.iteritems()]

    def get_course_stat(self):
        return (self.course_stat['total'], self.course_stat['active_students'],
                self.course_stat['avg_score'],
                [(group, stat['total'], stat['active_students'], stat['avg_score'])
                 for (group, stat) in self.group_stat.iteritems()])

    def _student_stat(self, tasks):
        total = 0.0
        tasks_list = []

        for task in tasks:
            total += task.score
            tasks_list.append((task.task, task.score))

        return (total, tasks_list)

    def _group_update(self, group):
        stat = {
            'total': 0.0,
            'active_students': 0,
            'avg_score': 0.0,
            'student_stat': [],
        }

        group_students = []

        for student in group.students.filter(is_active=True).order_by('last_name', 'first_name'):
            tasks = TaskTaken.objects.filter(user=student).filter(task__in=self.tasks) \
                .filter(Q(Q(status=TaskTaken.STATUS_TAKEN) | Q(status=TaskTaken.STATUS_SCORED)))
            if tasks.count() > 0:
                stat['active_students'] += 1

            (scores, student_tasks) = self._student_stat(tasks)
            group_students.append((student, scores, student_tasks))
            stat['total'] += scores

        stat['student_stat'] = group_students

        if stat['active_students'] > 0:
            stat['avg_score'] = stat['total'] / stat['active_students']

        self.group_stat[group] = stat

    def _course_update(self, group):
        stat = self.group_stat[group]

        self.course_stat['total'] += stat['total']
        self.course_stat['active_students'] += stat['active_students']

        if self.course_stat['active_students'] > 0:
            self.course_stat['avg_score'] = self.course_stat['total'] / self.course_stat['active_students']
        else:
            self.course_stat['avg_score'] = 0.0
