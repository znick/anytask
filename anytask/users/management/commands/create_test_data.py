"""
A management command which deletes expired accounts (e.g.,
accounts which signed up but never activated) from the database.

Calls ``RegistrationProfile.objects.delete_expired_users()``, which
contains the actual logic for determining which accounts are deleted.

"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from years.models import Year
from schools.models import School
from groups.models import Group
from courses.models import Course
from tasks.models import Task, TaskGroupRelations
from issues.models import Issue, Event, IssueField


def parse_name(name):
    last_name, first_name = name.split(' ', 1)
    username = "_".join([first_name.lower(), last_name.lower()])
    return last_name, first_name, username


def save_all(collection):
    for item in collection:
        item.save()


class Command(BaseCommand):
    help = "Creating test database."

    def handle(self, **options):
        # Raw data
        years_raw = [2019, 2020]
        courses_raw = [{"name": "Charms", "year": 0,
                        "groups": (0, 2)},
                       {"name": "Potions", "year": 1,
                        "groups": (1,)},
                       {"name": "Transfigurations", "year": 1,
                        "groups": (3,)}]
        schools_raw = [{"name": "High School of Hersheba",
                        "link": "hersheba",
                        "courses": (0, 1)},
                       {"name": "Fourecks University",
                        "link": "fourecks",
                        "courses": (0, 2)}]
        groups_raw = [{"name": "Hersheba2019", "year": 0},
                      {"name": "Hersheba2020", "year": 1},
                      {"name": "Fourecks2019", "year": 0},
                      {"name": "Fourecks2020", "year": 1}]
        students_raw = [{"name": "Sia Hyde", "group": 0},
                        {"name": "Wasim Klein", "group": 0},
                        {"name": "Ella Eastwood", "group": 0},
                        {"name": "Maha Wilkes", "group": 1},
                        {"name": "Meg Sutherland", "group": 1},
                        {"name": "Kya Parsons", "group": 1},
                        {"name": "Ferne Huff", "group": 2},
                        {"name": "Jethro Higgs", "group": 2},
                        {"name": "Prince Knox", "group": 2},
                        {"name": "Layla Schmitt", "group": 3},
                        {"name": "Darci Stark", "group": 3},
                        {"name": "Ezmae Bradford", "group": 3}]
        teachers_raw = [{"name": "Eira Buckner", "courses": (0,)},
                        {"name": "Paul Akhtar", "courses": (1,)},
                        {"name": "Kristi Todd", "courses": (2,)}]
        tasks_raw = [{"title": "Charms | Task 1", "course": 0, 
                      "groups": (0,), "updated_by": 0}]
        issues_raw = [{"student": 0, "task": 0}]

        # Create object from raw data

        print("Create years {}".format(years_raw))
        years = [Year.objects.create(start_year=start_year)
                 for start_year in years_raw]
        save_all(years)

        print("Create courses {}".format(courses_raw))
        courses = [Course.objects.create(name=course["name"],
                                         year=years[course["year"]],
                                         is_active=True)
                   for course in courses_raw]
        save_all(courses)

        print("Create schools {}".format(schools_raw))
        schools = [School.objects.create(name=school["name"],
                                         link=school["link"])
                   for school in schools_raw]
        save_all(schools)

        print("Create groups {}".format(groups_raw))
        groups = [Group.objects.create(name=group["name"],
                                       year=years[group["year"]])
                  for group in groups_raw]
        save_all(groups)

        print("Create users")
        students = []
        teachers = []
        for user_raw in students_raw + teachers_raw:
            last_name, first_name, username = parse_name(user_raw["name"])
            user = User.objects.create(username=username)
            user.last_name = last_name
            user.first_name = first_name
            user.set_password(username)

            if user_raw in students_raw:
                students.append(user)
            else:
                teachers.append(user)
        save_all(students)
        save_all(teachers)

        print("Create tasks {}".format(tasks_raw))
        tasks = [Task.objects.create(title=task["title"],
                                     course=courses[task["course"]])
                 for task in tasks_raw]
        save_all(tasks)

        print("Create issues {}".format(issues_raw))
        issues = [Issue.objects.create(student=students[issue["student"]],
                                       task=tasks[issue["task"]])
                 for issue in issues_raw]
        save_all(issues)

        # Bind objects

        print("Bind schools and courses")
        for school_id, school in enumerate(schools_raw):
            for course_id in school["courses"]:
                schools[school_id].courses.add(courses[course_id])

        print("Bind courses and groups")
        for course_id, course in enumerate(courses_raw):
            for group_id in course["groups"]:
                courses[course_id].groups.add(groups[group_id])

        print("Bind students and groups")
        for student_id, student in enumerate(students_raw):
            user = students[student_id]
            group = groups[student["group"]]
            group.students.add(user)

        print("Set teachers")
        for teacher_id, teacher in enumerate(teachers_raw):
            user = teachers[teacher_id]
            for course_id in teacher["courses"]:
                course = courses[course_id]
                course.teachers.add(user)

        print("Bind tasks with courses")
        for task_id, task in enumerate(tasks_raw):
            course = courses[task["course"]]
            task = tasks[task_id]
            course.task_set.add(task)

        print("Bind tasks with groups")
        for task_id, task in enumerate(tasks_raw):
            task = tasks[task_id]
            for group_id in tasks_raw[task_id]["groups"]:
                group = groups[group_id]
                relation = TaskGroupRelations.objects.create(
                    task=task, group=group)
                relation.save()
                

        print("Completed creating test data.")
