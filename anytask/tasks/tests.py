# -*- coding: utf-8 -*-

"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from schools.models import School
from courses.models import Course
from groups.models import Group
from years.models import Year
from tasks.models import Task, TaskGroupRelations

from mock import patch
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from django.core.urlresolvers import reverse

import tasks.views
import courses.views


def save_result_html(html):
    with open(r'../test_page.html', 'w') as f:
        f.write(html)


class CreateTest(TestCase):
    def test_task_create_filled(self):
        year = Year.objects.create(start_year=2016)
        group = [Group.objects.create(name='name_groups', year=year)]
        course = Course.objects.create(name='course_name',
                                       year=year)
        course.groups = group
        course.save()

        parent_task = Task.objects.create(title='parent_task',
                                          course=course)

        deadline_time = datetime.now() + timedelta(days=5)

        task = Task()
        task.title = 'title'
        task.course = course
        task.weight = 1
        task.is_hidden = True
        task.parent_task = parent_task
        task.task_text = 'task_text'
        task.score_max = 10
        task.contest_integrated = True
        task.rb_integrated = True
        task.type = Task.TYPE_SIMPLE
        task.deadline_time = deadline_time
        task.contest_id = 1234
        task.problem_id = 'A'
        task.sended_notify = False
        task.one_file_upload = True
        task.save()
        task.groups = group
        task_id = task.id

        task = Task.objects.get(id=task_id)

        self.assertIsInstance(task, Task)
        self.assertEqual(task.title, 'title')
        self.assertEqual(task.course, course)
        self.assertCountEqual(task.groups.all(), group)
        self.assertEqual(task.weight, 1)
        self.assertEqual(task.is_hidden, True)
        self.assertEqual(task.parent_task, parent_task)
        self.assertEqual(task.task_text, 'task_text')
        self.assertEqual(task.contest_integrated, True)
        self.assertEqual(task.rb_integrated, True)
        self.assertEqual(task.type, Task.TYPE_SIMPLE)
        self.assertEqual(task.deadline_time.replace(tzinfo=None), deadline_time - timedelta(hours=3))
        self.assertEqual(task.contest_id, 1234)
        self.assertEqual(task.problem_id, 'A')
        self.assertEqual(task.sended_notify, False)
        self.assertEqual(task.one_file_upload, True)


class ViewsTest(TestCase):
    def setUp(self):
        self.teacher_password = 'password1'
        self.teacher = User.objects.create_user(username='teacher',
                                                password=self.teacher_password)
        self.teacher.first_name = 'teacher_name'
        self.teacher.last_name = 'teacher_last_name'
        self.teacher.save()

        self.student_password = 'password2'
        self.student = User.objects.create_user(username='student',
                                                password=self.student_password)
        self.student.first_name = 'student_name'
        self.student.last_name = 'student_last_name'
        self.student.save()

        self.year = Year.objects.create(start_year=2016)

        self.group = Group.objects.create(name='group_name',
                                          year=self.year)
        self.group.students = [self.student]
        self.group.save()

        self.course = Course.objects.create(name='course_name',
                                            year=self.year)
        self.course.groups = [self.group]
        self.course.teachers = [self.teacher]
        self.course.save()

        self.school = School.objects.create(name='school_name',
                                            link='school_link')
        self.school.courses = [self.course]
        self.school.save()

        self.task = Task.objects.create(title='task_title_0',
                                        course=self.course,
                                        score_max=15)
        self.task.set_position_in_new_group()

    def test_task_create_page_anonymously(self):
        client = self.client

        # get page
        response = client.get(reverse(tasks.views.task_create_page, kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 302, "Need login for task_create_page")

    def test_task_import_page_anonymously(self):
        client = self.client

        # get page
        response = client.get(reverse(tasks.views.task_import_page, kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 302, "Need login for task_import_page")

    def test_task_edit_page_anonymously(self):
        client = self.client

        # get page
        response = client.get(reverse(tasks.views.task_edit_page, kwargs={'task_id': self.task.id}))
        self.assertEqual(response.status_code, 302, "Need login for task_edit_page")

    def test_task_create_or_edit_page_with_teacher(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.teacher.username, password=self.teacher_password),
                        "Can't login via teacher")

        # get create task page
        response = client.get(reverse(tasks.views.task_create_page, kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200, "Can't get task_create_page via teacher")

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container', recursive=False)

        # title
        self.assertEqual(html.find('title').string.strip().strip('\n'),
                         u'sozdanie_zadachi | course_name | 2016-2017',
                         'Wrong page title')

        # navbar
        navbar = html.nav
        navbar_links = navbar.ul('li')
        self.assertEqual(len(navbar_links), 1, 'navbar must have only 1 link')
        self.assertEqual(navbar_links[0].a['href'], '/course/1#tasks-tab', 'navbar link wrong')

        # breadcrumbs
        breadcrumbs = container.find('ul', 'breadcrumb')('li')
        self.assertEqual(len(breadcrumbs), 4, 'breadcrumbs len is not 4')
        self.assertEqual(breadcrumbs[0].a['href'], u'/', 'breadcrumbs 1st link wrong')
        self.assertEqual(breadcrumbs[1].a['href'], u'/school/school_link', 'breadcrumbs 2nd link wrong')
        self.assertEqual(breadcrumbs[1].a.string.strip().strip('\n'), u'school_name', 'breadcrumbs 2nd text wrong')
        self.assertEqual(breadcrumbs[2].a['href'], u'/course/1', 'breadcrumbs 3rd link wrong')
        self.assertEqual(breadcrumbs[2].a.string.strip().strip('\n'), u'course_name', 'breadcrumbs 3rd text wrong')
        self.assertEqual(breadcrumbs[3].string.strip().strip('\n'), u'sozdanie_zadachi', 'breadcrumbs 4th text wrong')

        # form
        div_task_id = container.find('div', {'id': 'task_edit'})
        self.assertIsNotNone(div_task_id, "No main div with id 'task_edit'")
        self.assertEqual(container.find('h5', 'card-title').string,
                         u'sozdanie_zadachi',
                         "Wrong card title")

        form_inputs = div_task_id.form('input', 'form-control')
        for input_simple in form_inputs:
            self.assertEqual(input_simple['value'], '', "form inputs id='{}' not empty".format(input_simple['id']))

        form_checkbox = div_task_id.form('input', {'type': 'checkbox'})
        for checkbox in form_checkbox:
            self.assertFalse('checked' in checkbox, "form checkbox id='{}' not empty".format(checkbox['id']))

        form_select_group = div_task_id.form.find('select', {'id': 'task_edit_group'})('option')
        self.assertEqual(len(form_select_group), 1, "form select group len not 2")
        self.assertEqual(form_select_group[0]['value'], '1', 'form select group 1nd option value wrong')
        self.assertTrue('selected' in dict(form_select_group[0].attrs), 'form select group 1nd option selected')
        self.assertEqual(form_select_group[0].string.strip().strip('\n'),
                         u'group_name',
                         'form select group 2nd option text wrong')

        form_select_type = div_task_id.form.find('select', {'id': 'task_edit_type'})('option')
        self.assertEqual(len(form_select_type), 4, "form select type len not 4")
        self.assertEqual(form_select_type[0]['value'], 'All', 'form select type 1st option value wrong')
        self.assertEqual(form_select_type[0].string.strip().strip('\n'),
                         u's_obsuzhdeniem',
                         'form select type 1st option text wrong')
        self.assertEqual(form_select_type[1]['value'], 'Only mark', 'form select type 2nd option value wrong')
        self.assertFalse('selected' in form_select_type[1], 'form select type 2nd option selected')
        self.assertEqual(form_select_type[1].string.strip().strip('\n'),
                         u'tolko_ocenka',
                         'form select type 2nd option text wrong')

        form_textarea = div_task_id.form.textarea
        self.assertIsNone(form_textarea.string, "form textarea not empty")

        # post create task page
        response = client.post(reverse(tasks.views.task_create_page, kwargs={'course_id': self.course.id}),
                               {'task_title': 'task_title',
                                'max_score': '10',
                                'task_group_id[]': ['1'],
                                'deadline': '01-08-2016 5:30',
                                'changed_task': 'on',
                                'task_type': 'All',
                                'contest_integrated': 'on',
                                'contest_id': '1234',
                                'problem_id': 'A',
                                'rb_integrated': 'on',
                                'one_file_upload': 'on',
                                'hidden_task': 'on',
                                'parent_id': "",
                                'task_text': 'task_text'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content,
                         b'{"page_title": "task_title | course_name | 2016-2017", "redirect_page": "/task/edit/2"}')

        # check created task
        self.assertEqual(len(Task.objects.all()), 2, 'Must be 2 tasks')
        created_task = Task.objects.get(id=2)
        self.assertEqual(created_task.title, 'task_title', 'Created task wrong title')
        self.assertEqual(created_task.course, self.course, 'Created task wrong course')
        self.assertCountEqual(created_task.groups.all(), [self.group], 'Created task wrong group')
        self.assertEqual(created_task.is_hidden, True, 'Created task wrong is_hidden')
        self.assertIsNone(created_task.parent_task, 'Created task wrong parent_task')
        self.assertEqual(created_task.task_text, 'task_text', 'Created task wrong task_text')
        self.assertEqual(created_task.contest_integrated, True, 'Created task wrong contest_integrated')
        self.assertEqual(created_task.rb_integrated, True, 'Created task wrong rb_integrated')
        self.assertEqual(created_task.type, Task.TYPE_FULL, 'Created task wrong type')
        self.assertEqual(created_task.deadline_time.replace(tzinfo=None), datetime(2016, 8, 1, 2, 30),
                         'Created task wrong deadline_time')
        self.assertEqual(created_task.contest_id, 1234, 'Created task wrong contest_id')
        self.assertEqual(created_task.problem_id, 'A', 'Created task wrong problem_id')
        self.assertEqual(created_task.sended_notify, False, 'Created task wrong sended_notify')
        self.assertEqual(created_task.one_file_upload, True, 'Created task wrong one_file_upload')
        task_pos = TaskGroupRelations.objects.filter(task=created_task)
        self.assertEqual(len(task_pos), 1, 'Created task TaskGroupRelations len not 1')
        self.assertEqual(task_pos[0].group, self.group, 'Created task TaskGroupRelations groups not equal')
        self.assertEqual(task_pos[0].position, 1, 'Created task TaskGroupRelations position not 1')
        self.assertFalse(task_pos[0].deleted, 'Created task TaskGroupRelations deleted')

        # get edit task page
        response = client.get(reverse(tasks.views.task_edit_page, kwargs={'task_id': created_task.id}))
        self.assertEqual(response.status_code, 200, "Can't get task_edit_page via teacher")

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container', recursive=False)

        # title
        self.assertEqual(html.find('title').string.strip().strip('\n'),
                         u'task_title | course_name | 2016-2017',
                         'Wrong page title')

        # navbar
        navbar = html.nav
        navbar_links = navbar.ul('li')
        self.assertEqual(len(navbar_links), 1, 'navbar must have only 1 link')
        self.assertEqual(navbar_links[0].a['href'], '/course/1#tasks-tab', 'navbar link wrong')

        # breadcrumbs
        breadcrumbs = container.find('ul', 'breadcrumb')('li')
        self.assertEqual(len(breadcrumbs), 4, 'breadcrumbs len is not 4')
        self.assertEqual(breadcrumbs[0].a['href'], u'/', 'breadcrumbs 1st link wrong')
        self.assertEqual(breadcrumbs[1].a['href'], u'/school/school_link', 'breadcrumbs 2nd link wrong')
        self.assertEqual(breadcrumbs[1].a.string.strip().strip('\n'), u'school_name', 'breadcrumbs 2nd text wrong')
        self.assertEqual(breadcrumbs[2].a['href'], u'/course/1', 'breadcrumbs 3rd link wrong')
        self.assertEqual(breadcrumbs[2].a.string.strip().strip('\n'), u'course_name', 'breadcrumbs 3rd text wrong')
        self.assertEqual(breadcrumbs[3].string.strip().strip('\n'),
                         u'redaktirovanie_zadachi',
                         'breadcrumbs 4th text wrong')

        # form
        div_task_id = container.find('div', {'id': 'task_edit'})
        self.assertIsNotNone(div_task_id, "No main div with id 'task_edit'")
        self.assertEqual(container.find('h5', 'card-title').string,
                         u'redaktirovanie_zadachi',
                         "Wrong card title")

        form_inputs = div_task_id.form('input', 'form-control')
        self.assertEqual(form_inputs[0]['value'], 'task_title', "form input id='{}' wrong".format(form_inputs[0]['id']))
        self.assertEqual(form_inputs[2]['value'], '10', "form input id='{}' wrong".format(form_inputs[2]['id']))
        self.assertEqual(form_inputs[3]['value'], '01-08-2016 05:30',
                         "form input id='{}' wrong".format(form_inputs[3]['id']))
        self.assertEqual(form_inputs[5]['value'], '1234', "form input id='{}' wrong".format(form_inputs[5]['id']))
        self.assertEqual(form_inputs[6]['value'], 'A', "form input id='{}' wrong".format(form_inputs[6]['id']))

        form_checkbox = div_task_id.form('input', {'type': 'checkbox'})

        for i in range(len(form_checkbox)):
            if form_checkbox[i]['id'] == "task_edit_changed_task":
                self.assertFalse('checked' in form_checkbox[i],
                                 "form checkbox id='{}' checked".format(form_checkbox[i]['id']))
            else:
                self.assertTrue('checked' in dict(form_checkbox[i].attrs),
                                "form checkbox id='{}' not checked".format(form_checkbox[i]['id']))

        form_select_group = div_task_id.form.find('select', {'id': 'task_edit_group'})('option')
        self.assertEqual(len(form_select_group), 1, "form select group len not 2")
        self.assertEqual(form_select_group[0]['value'], '1', 'form select group 2nd option value wrong')
        self.assertTrue('selected' in dict(form_select_group[0].attrs), 'form select group 2nd option selected')
        self.assertEqual(form_select_group[0].string.strip().strip('\n'),
                         u'group_name',
                         'form select group 2nd option text wrong')

        form_select_type = div_task_id.form.find('select', {'id': 'task_edit_type'})('option')
        self.assertEqual(len(form_select_type), 4, "form select type len not 4")
        self.assertEqual(form_select_type[0]['value'], 'All', 'form select type 1st option value wrong')
        self.assertTrue('selected' in dict(form_select_group[0].attrs), 'form select type 1nd option not selected')
        self.assertEqual(form_select_type[0].string.strip().strip('\n'),
                         u's_obsuzhdeniem',
                         'form select type 1st option text wrong')
        self.assertEqual(form_select_type[1]['value'], 'Only mark', 'form select type 2nd option value wrong')
        self.assertFalse('selected' in dict(form_select_type[1].attrs), 'form select type 2nd option selected')
        self.assertEqual(form_select_type[1].string.strip().strip('\n'),
                         u'tolko_ocenka',
                         'form select type 2nd option text wrong')

        form_textarea = div_task_id.form.textarea
        self.assertEqual(form_textarea.string, 'task_text', "form textarea empty")

        # get course and show hidden task page
        response = client.post(reverse(courses.views.change_visibility_hidden_tasks),
                               {'course_id': self.course.id})
        self.assertEqual(response.status_code, 200, "Can't get change_visibility_hidden_tasks via teacher")
        self.assertEqual(response.content, b'OK')
        response = client.get(reverse(courses.views.gradebook, kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200, "Can't get course_page via teacher")

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container-fluid', recursive=False)

        # table results
        table = container.find('table', 'table-results')

        table_head = table.thead('th')[2]
        self.assertEqual(table_head.a.string.strip().strip('\n'), 'task_title_0', 'Wrong title 1st task')
        self.assertEqual(table_head.span.string.strip().strip('\n'), '15', 'Wrong score_max 1st task')

        table_body = table.tbody('td')[2]
        self.assertEqual(table_body.a['href'],
                         '/issue/get_or_create/1/2',
                         'Wrong link to issue in table for 1st task')
        self.assertEqual(table_body.span.string.strip().strip('\n'), '0', 'Wrong mark in table for 1st task')
        self.assertIn('no-issue', table_body.span['class'], "No 'no-issue' class in table for 1st task")

        table_head = table.thead('th')[3]
        self.assertEqual(table_head.a.string.strip().strip('\n'), 'task_title', 'Wrong title 2nd task')
        self.assertEqual(table_head.span.string.strip().strip('\n'), '10', 'Wrong score_max 2nd task')

        table_body = table.tbody('td')[3]
        self.assertIsNone(table_body.a, 'No empty link to issue in table for 2nd task')
        self.assertEqual(table_body.span.string.strip().strip('\n'), '0', 'Wrong mark in table for 2nd task')

    def test_task_create_page_with_student(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.student.username, password=self.student_password),
                        "Can't login via student")

        # get page
        response = client.get(reverse(tasks.views.task_create_page, kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 403, "Only teacher can get task_create_page")

    def test_task_import_page_with_student(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.student.username, password=self.student_password),
                        "Can't login via student")

        # get page
        response = client.get(reverse(tasks.views.task_import_page, kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 403, "Only teacher can get task_import_page")

    def test_task_edit_page_with_student(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.student.username, password=self.student_password),
                        "Can't login via student")

        # get page
        response = client.get(reverse(tasks.views.task_edit_page, kwargs={'task_id': self.task.id}))
        self.assertEqual(response.status_code, 403, "Only teacher can get task_edit_page")

    @patch('tasks.views.get_contest_info')
    def test_import_contest(self, mock_get_contest_info):
        import tasks  # Не знаю почему, но ниже в этом методе он требует чтобы это было
        client = self.client
        post_data = {'contest_id_for_task': '1100',
                     'course_id': '1',
                     'contest_problems[]': ['1055/2013_02_24/rqW5cRAAgR', '1055/2013_02_24/NuAYb8aSXw'],
                     'max_score': '10',
                     'task_group_id[]': ['1'],
                     'deadline': '05-07-2016 05:30',
                     'changed_task': 'on',
                     'rb_integrated': 'on',
                     'hidden_task': 'on',
                     'parent_id': ""}

        problems = [{'problemId': '1055/2013_02_24/NuAYb8aSXw',
                     'problemTitle': 'Task1',
                     'statement': 'text1',
                     'alias': 'A'},
                    {'problemId': '1055/2013_02_24/dY74Gd2fyz',
                     'problemTitle': 'Task2',
                     'statement': 'text2',
                     'alias': 'B'},
                    {'problemId': '1055/2013_02_24/rqW5cRAAgR',
                     'problemTitle': 'Task3',
                     'statement': 'text3',
                     'alias': 'C'}]

        # login
        self.assertTrue(client.login(username=self.teacher.username, password=self.teacher_password),
                        "Can't login via teacher")

        # get contest_task_import page with known error
        mock_get_contest_info.return_value = (False, "You're not allowed to view this contest.")
        response = client.post(reverse(tasks.views.contest_task_import), post_data)
        self.assertEqual(response.status_code, 200, "Can't get get_contest_info via teacher")
        self.assertEqual(response.content,
                         b'{"is_error": true, "error": "net_prav_na_kontest"}',
                         'Wrong response text')

        # get contest_task_import page with unknown error
        mock_get_contest_info.return_value = (False, "404")
        response = client.post(reverse(tasks.views.contest_task_import), post_data)
        self.assertEqual(response.status_code, 403, "Must be forbidden")

        # get contest_task_import page with unknown error
        mock_get_contest_info.return_value = (True, {'problems': problems})
        response = client.post(reverse(tasks.views.contest_task_import), post_data)
        self.assertEqual(response.status_code, 200, "Can't get get_contest_info via teacher")
        self.assertEqual(response.content, b'OK', 'Wrong response text')

        tasks = Task.objects.exclude(id=1)
        self.assertEqual(len(tasks), 2, 'Wrong number of tasks')
        problems_idx = 0
        for idx, task in enumerate(tasks):
            self.assertEqual(task.title, problems[problems_idx]['problemTitle'], 'Wrong task title')
            self.assertEqual(task.course, self.course)
            self.assertCountEqual(task.groups.all(), [self.group])
            self.assertEqual(task.is_hidden, True)
            self.assertIsNone(task.parent_task)
            self.assertEqual(task.task_text, problems[problems_idx]['statement'])
            self.assertEqual(task.contest_integrated, True)
            self.assertEqual(task.rb_integrated, True)
            self.assertEqual(task.type, Task.TYPE_FULL)
            self.assertEqual(task.deadline_time.replace(tzinfo=None),
                             datetime.strptime(post_data['deadline'], '%d-%m-%Y %H:%M') - timedelta(hours=3))
            self.assertEqual(str(task.contest_id), post_data['contest_id_for_task'])
            self.assertEqual(task.problem_id, problems[problems_idx]['alias'])
            self.assertEqual(task.sended_notify, False)
            task_pos = TaskGroupRelations.objects.filter(task=task)
            self.assertEqual(len(task_pos), 1, 'Created task TaskGroupRelations len not 1')
            self.assertEqual(task_pos[0].group, self.group, 'Created task TaskGroupRelations groups not equal')
            self.assertEqual(task_pos[0].position, idx + 1, idx)
            self.assertFalse(task_pos[0].deleted, 'Created task TaskGroupRelations deleted')
            problems_idx = 2
