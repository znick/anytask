# -*- coding: utf-8 -*-

import datetime

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings
from schools.models import School
from courses.models import Course, IssueField, FilenameExtension, CourseMarkSystem, MarkField, IssueStatusSystem,\
    DefaultTeacher
from issues.models import Issue, IssueStatus
from groups.models import Group
from years.models import Year
from tasks.models import Task, TaskTaken
from tasks.management.commands.check_task_taken_expires import Command as CheckTastTakenExpiresCommand

from BeautifulSoup import BeautifulSoup
from django.core.urlresolvers import reverse


def save_result_html(html):
    with open(r'../test_page.html', 'w') as f:
        print html
        f.write(html)


class CreateTest(TestCase):
    def setUp(self):
        self.user_password = 'password'
        self.user = User.objects.create_user(
            username='test_user', password=self.user_password)
        self.year = Year.objects.create(start_year=2016)

    def test_course_create_filled(self):
        year = self.year
        teachers = [User.objects.create(username='test_teachers', password='password')]
        groups = [Group.objects.create(name='name_groups', year=year)]
        group_with_extern = Group.objects.create(name='name_group_with_extern', year=year)
        issue_fields = [IssueField.objects.create(name='name_issue_fields')]
        filename_extensions = [FilenameExtension.objects.create(name='name_filename_extensions')]
        mark_system = CourseMarkSystem.objects.create(name='name_mark_system')

        course = Course()
        course.name = 'name'
        course.name_id = 'name_id'
        course.information = 'information'
        course.is_active = True
        course.year = year
        course.save()
        course.teachers = teachers
        course.groups = groups
        course.issue_fields = issue_fields
        # course.contest_integrated = True
        # course.send_rb_and_contest_together = True
        # course.rb_integrated = True
        course.send_to_contest_from_users = True
        course.filename_extensions = filename_extensions
        course.full_transcript = False
        course.private = True
        course.can_be_chosen_by_extern = True
        course.group_with_extern = group_with_extern
        course.mark_system = mark_system
        course.save()
        course_id = course.id

        course = Course.objects.get(id=course_id)

        self.assertIsInstance(course, Course)
        self.assertEqual(course.name, 'name')
        self.assertEqual(course.name_id, 'name_id')
        self.assertEqual(course.information, 'information')
        self.assertEqual(course.year, year)
        self.assertEqual(course.is_active, True)
        self.assertItemsEqual(course.teachers.all(), teachers)
        self.assertItemsEqual(course.groups.all(), groups)
        self.assertItemsEqual(course.issue_fields.all(), IssueField.objects.exclude(id=10).exclude(id=11))
        self.assertEqual(course.contest_integrated, False)
        self.assertEqual(course.send_rb_and_contest_together, False)
        self.assertEqual(course.rb_integrated, False)
        self.assertEqual(course.send_to_contest_from_users, True)
        self.assertItemsEqual(course.filename_extensions.all(), filename_extensions)
        self.assertEqual(course.full_transcript, False)
        self.assertEqual(course.private, True)
        self.assertEqual(course.can_be_chosen_by_extern, True)
        self.assertEqual(course.group_with_extern, group_with_extern)
        self.assertEqual(course.mark_system, mark_system)


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

    def test_gradebook_anonymously(self):
        client = self.client

        # get page
        response = client.get(reverse('courses.views.gradebook', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 302)

    def test_queue_page_anonymously(self):
        client = self.client

        # get page
        response = client.get(reverse('courses.views.queue_page', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 302)

    def test_edit_course_information_anonymously(self):
        client = self.client

        # get page
        response = client.get(reverse('courses.views.edit_course_information'))
        self.assertEqual(response.status_code, 405)

        # post page
        response = client.post(reverse('courses.views.edit_course_information'),
                               {'course_id': self.course.id,
                                'course_information': 'course_information'})
        self.assertEqual(response.status_code, 302)

    def test_course_settings_anonymously(self):
        client = self.client

        # get page
        response = client.get(reverse('courses.views.course_settings', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 302)

    def test_change_visibility_hidden_tasks_anonymously(self):
        client = self.client

        # get page
        response = client.get(reverse('courses.views.change_visibility_hidden_tasks'))
        self.assertEqual(response.status_code, 405)

        # post page
        response = client.post(reverse('courses.views.change_visibility_hidden_tasks'),
                               {'course_id': self.course.id})
        self.assertEqual(response.status_code, 302)

    def test_set_course_mark_anonymously(self):
        client = self.client

        # get page
        response = client.get(reverse('courses.views.set_course_mark'))
        self.assertEqual(response.status_code, 405)

        # post page
        response = client.post(reverse('courses.views.set_course_mark'),
                               {'course_id': self.course.id,
                                'group_id': self.group.id,
                                'student_id': self.student.id,
                                'mark_id': '1'})
        self.assertEqual(response.status_code, 302)

    def test_set_task_mark_anonymously(self):
        client = self.client

        # get page
        response = client.get(reverse('courses.views.set_task_mark'))
        self.assertEqual(response.status_code, 405)

        # post page
        response = client.post(reverse('courses.views.set_task_mark'),
                               {'task_id': '1',
                                'student_id': self.student.id,
                                'mark_max': '10',
                                'mark_value': '3'})
        self.assertEqual(response.status_code, 302)

    def test_gradebook_with_teacher(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.teacher.username, password=self.teacher_password))

        # get page
        response = client.get(reverse('courses.views.gradebook', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container-fluid', recursive=False)

        # title
        self.assertEqual(html.find('title').string.strip().strip('\n'), u'course_name | 2016-2017')

        # navbar
        navbar = html.nav
        navbar_links = navbar.ul('li')
        self.assertEqual(len(navbar_links), 4)
        self.assertEqual(navbar_links[0].a['href'], u'/course/1')
        self.assertEqual(navbar_links[1].a['href'], u'/course/1/gradebook/')
        self.assertEqual(navbar_links[2].a['href'], u'/course/1/queue')
        self.assertEqual(navbar_links[3].a['href'], u'/course/1/settings')

        navbar_dropdown = navbar.find('li', 'dropdown')
        self.assertEqual(navbar_dropdown.find('div', 'dropdown-menu').h6.string.strip().strip('\n'),
                         u'teacher_name teacher_last_name')
        navbar_dropdown_inside = navbar_dropdown.find('div', 'dropdown-menu')('a')
        self.assertEqual(len(navbar_dropdown_inside), 4)
        self.assertEqual(navbar_dropdown_inside[0]['href'], u'/accounts/profile')
        self.assertEqual(navbar_dropdown_inside[1]['href'], u'/user/settings')
        self.assertEqual(navbar_dropdown_inside[2]['href'], u'/accounts/password/change/')
        self.assertEqual(navbar_dropdown_inside[3]['href'], u'/accounts/logout/')

        # breadcrumbs
        breadcrumbs = container.find('ul', 'breadcrumb')('li')
        self.assertEqual(len(breadcrumbs), 4)
        self.assertEqual(breadcrumbs[0].a['href'], u'/')
        self.assertEqual(breadcrumbs[1].a['href'], u'/school/school_link')
        self.assertEqual(breadcrumbs[1].a.string.strip().strip('\n'), u'school_name')
        self.assertEqual(breadcrumbs[2].a.string.strip().strip('\n'), u'course_name')

        # course information
        self.assertIsNone(container.find('span', 'course-information'))

        # teachers
        # teachers = container.find('p', 'course_teachers')('a')
        # self.assertEqual(len(teachers), 1)
        # self.assertEqual(teachers[0]['href'], u'/accounts/profile/teacher')
        # self.assertEqual(teachers[0].string.strip().strip('\n'), u'teacher_last_name teacher_name')

        # edit course button
        # btn_group = container.find('div', {'id': 'btn_group_edit_course'})
        # self.assertIsNotNone(btn_group)
        # btn_group = btn_group('a')
        # self.assertEqual(len(btn_group), 1)
        # self.assertEqual(btn_group[0]['href'], u'/task/create/1')

        # table results
        table = container('table', 'table-results')
        self.assertEqual(len(table), 1)

        table_body_rows = table[0].tbody('tr')
        self.assertEqual(len(table_body_rows), 1)

        table_body_rows_cells = table_body_rows[0]('td')
        self.assertEqual(len(table_body_rows_cells), 4)
        self.assertEqual(table_body_rows_cells[1].a['href'], u'/users/student/')
        self.assertEqual(table_body_rows_cells[1].a.string.strip().strip('\n'), u'student_last_name&nbsp;student_name')
        self.assertEqual(table_body_rows_cells[2].string.strip().strip('\n'), u'&nbsp;')
        self.assertEqual(table_body_rows_cells[3].span.string.strip().strip('\n'), u'0')

    def test_queue_page_with_teacher(self):
        return
        client = self.client

        # login
        self.assertTrue(client.login(username=self.teacher.username, password=self.teacher_password))

        # get page
        response = client.get(reverse('courses.views.queue_page', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container', recursive=False)

        # title
        self.assertEqual(html.find('title').string.strip().strip('\n'), u'course_name | 2016-2017')

        # navbar
        navbar = html.nav
        navbar_links = navbar.ul('li')
        self.assertEqual(len(navbar_links), 4)
        self.assertEqual(navbar_links[0].a['href'], u'/course/1')
        self.assertEqual(navbar_links[1].a['href'], u'/course/1/gradebook')
        self.assertEqual(navbar_links[2].a['href'], '')
        self.assertEqual(navbar_links[3].a['href'], u'/course/1/settings')

        # breadcrumbs
        breadcrumbs = container.find('ul', 'breadcrumb')('li')
        self.assertEqual(len(breadcrumbs), 4)
        self.assertEqual(breadcrumbs[0].a['href'], u'/')
        self.assertEqual(breadcrumbs[1].a['href'], u'/school/school_link')
        self.assertEqual(breadcrumbs[1].a.string.strip().strip('\n'), u'school_name')
        self.assertEqual(breadcrumbs[2].a['href'], u'/course/1')
        self.assertEqual(breadcrumbs[2].a.string.strip().strip('\n'), u'course_name')
        self.assertEqual(breadcrumbs[3].string.strip().strip('\n'), u'ochered_na_proverku')

        # filter
        form = container.form
        self.assertIsNotNone(form)

        form_id_responsible = form.find('select', {'id': 'id_responsible'})('option')
        self.assertEqual(len(form_id_responsible), 2)
        self.assertEqual(form_id_responsible[0]['value'], '')
        self.assertTrue('selected' in dict(form_id_responsible[0].attrs))
        self.assertEqual(form_id_responsible[0].string.strip().strip('\n'), u'luboj')
        self.assertEqual(form_id_responsible[1]['value'], '1')
        self.assertFalse('selected' in form_id_responsible[1])
        self.assertEqual(form_id_responsible[1].string.strip().strip('\n'), u'teacher_name teacher_last_name')

        form_id_followers = form.find('div', {'id': 'div_id_followers'}).find('select')('option')
        self.assertEqual(len(form_id_followers), 1)
        self.assertEqual(form_id_followers[0]['value'], '1')
        self.assertFalse('checked' in form_id_responsible[0])
        self.assertEqual(form_id_followers[0].next.string.strip().strip('\n'), u'teacher_name teacher_last_name')

        # table queue
        table = container('table', 'table_queue')

        table_body_rows = table[0].tbody('tr')
        self.assertEqual(len(table_body_rows), 0)

    def test_edit_course_information_with_teacher(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.teacher.username, password=self.teacher_password))

        # get page
        response = client.get(reverse('courses.views.edit_course_information'))
        self.assertEqual(response.status_code, 405)

        # post page
        response = client.post(reverse('courses.views.edit_course_information'),
                               {'course_id': self.course.id,
                                'course_information': 'course_information'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"info": "<div class=\\"not-sanitize\\">course_information</div>"}')

        # get course page
        response = client.get(reverse('courses.views.gradebook', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

        # # course information
        # html = BeautifulSoup(response.content)
        # container = html.body.find('div', 'container', recursive=False)
        # self.assertEqual(container.find('div', {'id': 'course-information'}).find('div', 'not-sanitize')
        #                  .string.strip().strip('\n'), 'course_information')

    def test_course_settings_with_teacher(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.teacher.username, password=self.teacher_password))

        # get page
        response = client.get(reverse('courses.views.course_settings', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container', recursive=False)

        # title
        self.assertEqual(html.find('title').string.strip().strip('\n'), u'course_name | 2016-2017')

        # navbar
        navbar = html.nav
        navbar_links = navbar.ul('li')
        self.assertEqual(len(navbar_links), 4)
        self.assertEqual(navbar_links[0].a['href'], u'/course/1')
        self.assertEqual(navbar_links[1].a['href'], u'/course/1/gradebook')
        self.assertEqual(navbar_links[2].a['href'], u'/course/1/queue')
        self.assertEqual(navbar_links[3].a['href'], '')

        # breadcrumbs
        breadcrumbs = container.find('ul', 'breadcrumb')('li')
        self.assertEqual(len(breadcrumbs), 4)
        self.assertEqual(breadcrumbs[0].a['href'], u'/')
        self.assertEqual(breadcrumbs[1].a['href'], u'/school/school_link')
        self.assertEqual(breadcrumbs[1].a.string.strip().strip('\n'), u'school_name')
        self.assertEqual(breadcrumbs[2].a['href'], u'/course/1')
        self.assertEqual(breadcrumbs[2].a.string.strip().strip('\n'), u'course_name')
        self.assertEqual(breadcrumbs[3].string.strip().strip('\n'), u'nastrojki')

        # form
        form = container.form
        self.assertEqual(form['action'], '/course/1/settings')
        self.assertEqual(len(form.findAll('div', 'form-group')), 1)

        self.assertEqual(form.find('div', 'form-group').label.next.strip().strip('\n'), 'group_name')

        form_select = form.find('div', 'form-group')('option')
        self.assertEqual(form_select[0]['value'], '0')
        self.assertTrue('selected' in dict(form_select[0].attrs))
        self.assertEqual(form_select[0].string, '---')
        self.assertEqual(form_select[1]['value'], '1')
        self.assertFalse('selected' in form_select[1])
        self.assertEqual(form_select[1].string, 'teacher_name teacher_last_name')

        # post page
        response = client.post(reverse('courses.views.course_settings', kwargs={'course_id': self.course.id}),
                               {'group_1': '1'}, follow=True)
        self.assertEqual(response.status_code, 200)

        # get page
        response = client.get(reverse('courses.views.course_settings', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container', recursive=False)

        # form
        form_select = container.form.find('div', 'form-group')('option')
        self.assertEqual(form_select[0]['value'], '0')
        self.assertFalse('selected' in form_select[0])
        self.assertEqual(form_select[0].string, '---')
        self.assertEqual(form_select[1]['value'], '1')
        self.assertTrue('selected' in dict(form_select[1].attrs))
        self.assertEqual(form_select[1].string, 'teacher_name teacher_last_name')

    def test_change_visibility_hidden_tasks_with_teacher(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.teacher.username, password=self.teacher_password))

        # get page
        response = client.get(reverse('courses.views.change_visibility_hidden_tasks'))
        self.assertEqual(response.status_code, 405)

        Task.objects.create(title='task_title',
                            course=self.course,
                            is_hidden=True).set_position_in_new_group()

        # get course page
        response = client.get(reverse('courses.views.gradebook', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container-fluid', recursive=False)

        # edit course button
        btn_group = container.find('div', {'id': 'legend'})
        self.assertIsNotNone(btn_group)
        btn_group = btn_group('a')
        self.assertEqual(len(btn_group), 2)
        self.assertEqual(btn_group[0]['id'], u'status_btn')
        self.assertEqual(btn_group[1]['href'], u'javascript:change_visibility_hidden_tasks(1);')
        self.assertEqual(btn_group[1].string.strip().strip('\n'), u'pokazat_skrytye_zadachi')

        # table results
        table = container.find('table', 'table-results')

        table_head = table.thead('th')[2]
        self.assertIsNone(table_head.string)

        table_body = table.tbody('td')[2]
        self.assertEqual(table_body.string.strip().strip('\n'), u'&nbsp;')

        # post page
        response = client.post(reverse('courses.views.change_visibility_hidden_tasks'),
                               {'course_id': self.course.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'OK')

        # get course page
        response = client.get(reverse('courses.views.gradebook', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container-fluid', recursive=False)

        # edit course button
        btn_group = container.find('div', {'id': 'legend'})
        self.assertIsNotNone(btn_group)
        btn_group = btn_group('a')
        self.assertEqual(len(btn_group), 2)
        self.assertEqual(btn_group[0]['id'], u'status_btn')
        self.assertEqual(btn_group[1]['href'], u'javascript:change_visibility_hidden_tasks(1);')
        self.assertEqual(btn_group[1].string.strip().strip('\n'), u'ne_pokazyvat_skrytye_zadachi')

        # table results
        table = container.find('table', 'table-results')

        table_head = table.thead('th')[2]
        self.assertEqual(table_head.a.string.strip().strip('\n'), 'task_title')
        self.assertEqual(table_head.span.string.strip().strip('\n'), '0')

        table_body = table.tbody('td')[2]
        self.assertEqual(table_body.span.string.strip().strip('\n'), '0')

    def test_set_course_mark_with_teacher(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.teacher.username, password=self.teacher_password))

        # get page
        response = client.get(reverse('courses.views.set_course_mark'))
        self.assertEqual(response.status_code, 405)

        mark_fields = [MarkField.objects.create(name='mark1'), MarkField.objects.create(name='mark2')]
        course_mark_system = CourseMarkSystem.objects.create(name='course_mark_system')
        course_mark_system.marks = mark_fields
        course_mark_system.save()
        self.course.mark_system = course_mark_system
        self.course.save()

        # get course page
        response = client.get(reverse('courses.views.gradebook', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container-fluid', recursive=False)

        # table results
        table = container.find('table', 'table-results')

        table_body_rows_cells = table.tbody('td')
        table_course_mark_inputs = table_body_rows_cells[4]('input')
        table_course_mark_select = table_body_rows_cells[4].select('option')
        self.assertEqual(len(table_body_rows_cells), 5)
        self.assertEqual(table_body_rows_cells[4].span.string.strip().strip('\n'), u'--')
        self.assertEqual(len(table_course_mark_inputs), 4)
        self.assertEqual(table_course_mark_inputs[1]['name'], 'course_id')
        self.assertEqual(table_course_mark_inputs[1]['value'], '1')
        self.assertEqual(table_course_mark_inputs[2]['name'], 'group_id')
        self.assertEqual(table_course_mark_inputs[2]['value'], '1')
        self.assertEqual(table_course_mark_inputs[3]['name'], 'student_id')
        self.assertEqual(table_course_mark_inputs[3]['value'], '2')
        self.assertEqual(len(table_course_mark_select), 3)
        self.assertFalse('selected' in table_course_mark_select[0])
        self.assertEqual(table_course_mark_select[0]['value'], '-1')
        self.assertEqual(table_course_mark_select[0].string, '--')
        self.assertFalse('selected' in table_course_mark_select[1])
        self.assertEqual(table_course_mark_select[1]['value'], '1')
        self.assertEqual(table_course_mark_select[1].string, 'mark1')
        self.assertFalse('selected' in table_course_mark_select[2])
        self.assertEqual(table_course_mark_select[2]['value'], '2')
        self.assertEqual(table_course_mark_select[2].string, 'mark2')

        # post page
        response = client.post(reverse('courses.views.set_course_mark'),
                               {'course_id': self.course.id,
                                'group_id': self.group.id,
                                'student_id': self.student.id,
                                'mark_id': mark_fields[0].id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"mark_int": -1, "mark_id": 1, "mark": "mark1"}')

        # get course page
        response = client.get(reverse('courses.views.gradebook', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container-fluid', recursive=False)

        # table results
        table = container.find('table', 'table-results')

        table_body_rows_cells = table.tbody('td')
        table_course_mark_inputs = table_body_rows_cells[4]('input')
        table_course_mark_select = table_body_rows_cells[4].select('option')
        self.assertEqual(len(table_body_rows_cells), 5)
        self.assertEqual(table_body_rows_cells[4].span.string.strip().strip('\n'), u'mark1')
        self.assertEqual(len(table_course_mark_inputs), 4)
        self.assertEqual(table_course_mark_inputs[1]['name'], 'course_id')
        self.assertEqual(table_course_mark_inputs[1]['value'], '1')
        self.assertEqual(table_course_mark_inputs[2]['name'], 'group_id')
        self.assertEqual(table_course_mark_inputs[2]['value'], '1')
        self.assertEqual(table_course_mark_inputs[3]['name'], 'student_id')
        self.assertEqual(table_course_mark_inputs[3]['value'], '2')
        self.assertEqual(len(table_course_mark_select), 3)
        self.assertFalse('selected' in table_course_mark_select[0])
        self.assertEqual(table_course_mark_select[0]['value'], '-1')
        self.assertEqual(table_course_mark_select[0].string, '--')
        self.assertTrue('selected' in dict(table_course_mark_select[1].attrs))
        self.assertEqual(table_course_mark_select[1]['selected'], 'selected')
        self.assertEqual(table_course_mark_select[1]['value'], '1')
        self.assertEqual(table_course_mark_select[1].string, 'mark1')
        self.assertFalse('selected' in table_course_mark_select[2])
        self.assertEqual(table_course_mark_select[2]['value'], '2')
        self.assertEqual(table_course_mark_select[2].string, 'mark2')

    def test_set_task_mark_with_teacher(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.teacher.username, password=self.teacher_password))

        # get page
        response = client.get(reverse('courses.views.set_task_mark'))
        self.assertEqual(response.status_code, 405)

        task = Task.objects.create(title='task_title',
                                   course=self.course,
                                   score_max=10,
                                   type=Task.TYPE_SIMPLE)
        task.set_position_in_new_group()

        # get course page
        response = client.get(reverse('courses.views.gradebook', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container-fluid', recursive=False)

        # table results
        table = container.find('table', 'table-results')

        table_head = table.thead('th')[2]
        self.assertEqual(table_head.a.string.strip().strip('\n'), 'task_title')
        self.assertEqual(table_head.span.string.strip().strip('\n'), '10')

        table_body = table.tbody('td')[2]
        self.assertIsNotNone(table_body.find('div', 'task-mark-value'))
        self.assertEqual(table_body.find('div', 'task-mark-value').span.string.strip().strip('\n'), '0')
        self.assertIsNotNone(table_body.form)

        table_body_sum = table.tbody('td')[3]
        self.assertEqual(table_body_sum.span.string.strip().strip('\n'), '0')

        table_body_inputs = table_body.form.fieldset('input')
        self.assertEqual(len(table_body_inputs), 4)
        self.assertEqual(table_body_inputs[0]['name'], 'task_id')
        self.assertEqual(table_body_inputs[0]['value'], str(task.id))
        self.assertEqual(table_body_inputs[1]['name'], 'student_id')
        self.assertEqual(table_body_inputs[1]['value'], str(self.student.id))
        self.assertEqual(table_body_inputs[2]['name'], 'mark_max')
        self.assertEqual(table_body_inputs[2]['value'], str(task.score_max))
        self.assertEqual(table_body_inputs[3]['name'], 'mark_value')
        self.assertEqual(table_body_inputs[3]['value'], '0')

        # post page
        response = client.post(reverse('courses.views.set_task_mark'),
                               {'task_id': task.id,
                                'student_id': self.student.id,
                                'mark_max': task.score_max,
                                'mark_value': '3'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"color": "' + IssueStatus.objects.get(pk=5).color + '", "mark": 3.0}')

        # get course page
        response = client.get(reverse('courses.views.gradebook', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container-fluid', recursive=False)

        # table results
        table = container.find('table', 'table-results')

        table_head = table.thead('th')[2]
        self.assertEqual(table_head.a.string.strip().strip('\n'), 'task_title')
        self.assertEqual(table_head.span.string.strip().strip('\n'), '10')

        table_body = table.tbody('td')[2]
        self.assertIsNotNone(table_body.find('div', 'task-mark-value'))
        self.assertEqual(table_body.find('div', 'task-mark-value').span.string.strip().strip('\n'), '3')
        self.assertIsNotNone(table_body.form)

        table_body_sum = table.tbody('td')[3]
        self.assertEqual(table_body_sum.span.string.strip().strip('\n'), '3.0')

        table_body_inputs = table_body.form.fieldset('input')
        self.assertEqual(len(table_body_inputs), 4)
        self.assertEqual(table_body_inputs[0]['name'], 'task_id')
        self.assertEqual(table_body_inputs[0]['value'], str(task.id))
        self.assertEqual(table_body_inputs[1]['name'], 'student_id')
        self.assertEqual(table_body_inputs[1]['value'], str(self.student.id))
        self.assertEqual(table_body_inputs[2]['name'], 'mark_max')
        self.assertEqual(table_body_inputs[2]['value'], str(task.score_max))
        self.assertEqual(table_body_inputs[3]['name'], 'mark_value')
        self.assertEqual(table_body_inputs[3]['value'], '3')

    def test_gradebook_with_student(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.student.username, password=self.student_password))

        # get page
        response = client.get(reverse('courses.views.gradebook', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container-fluid', recursive=False)

        # title
        self.assertEqual(html.find('title').string.strip().strip('\n'), u'course_name | 2016-2017')

        # navbar
        navbar = html.nav
        navbar_links = navbar.ul('li')
        self.assertEqual(len(navbar_links), 2)
        self.assertEqual(navbar_links[0].a['href'], u'/course/1')
        self.assertEqual(navbar_links[1].a['href'], u'/course/1/gradebook/')

        navbar_dropdown = navbar.find('li', 'dropdown')
        self.assertEqual(navbar_dropdown.find('div', 'dropdown-menu').h6.string.strip().strip('\n'),
                         u'student_name student_last_name')
        navbar_dropdown_inside = navbar_dropdown.find('div', 'dropdown-menu')('a')
        self.assertEqual(len(navbar_dropdown_inside), 4)
        self.assertEqual(navbar_dropdown_inside[0]['href'], u'/accounts/profile')
        self.assertEqual(navbar_dropdown_inside[1]['href'], u'/user/settings')
        self.assertEqual(navbar_dropdown_inside[2]['href'], u'/accounts/password/change/')
        self.assertEqual(navbar_dropdown_inside[3]['href'], u'/accounts/logout/')

        # breadcrumbs
        breadcrumbs = container.find('ul', 'breadcrumb')('li')
        self.assertEqual(len(breadcrumbs), 4)
        self.assertEqual(breadcrumbs[0].a['href'], u'/')
        self.assertEqual(breadcrumbs[1].a['href'], u'/school/school_link')
        self.assertEqual(breadcrumbs[1].a.string.strip().strip('\n'), u'school_name')
        self.assertEqual(breadcrumbs[2].a.string.strip().strip('\n'), u'course_name')

        # course information
        self.assertIsNone(container.find('span', 'course-information'))

        # # teachers
        # teachers = container.find('p', 'course_teachers')('a')
        # self.assertEqual(len(teachers), 1)
        # self.assertEqual(teachers[0]['href'], u'/accounts/profile/teacher')
        # self.assertEqual(teachers[0].string.strip().strip('\n'), u'teacher_last_name teacher_name')

        # edit course button
        btn_group = container.find('div', 'btn-group')
        self.assertIsNone(btn_group)

        # table results
        table = container('table', 'table-results')
        self.assertEqual(len(table), 1)

        table_body_rows = table[0].tbody('tr')
        self.assertEqual(len(table_body_rows), 1)

        table_body_rows_cells = table_body_rows[0]('td')
        self.assertEqual(len(table_body_rows_cells), 4)
        self.assertEqual(table_body_rows_cells[1].a['href'], u'/users/student/')
        self.assertEqual(table_body_rows_cells[1].a.string.strip().strip('\n'), u'student_last_name&nbsp;student_name')
        self.assertEqual(table_body_rows_cells[2].string.strip().strip('\n'), u'&nbsp;')
        self.assertEqual(table_body_rows_cells[3].span.string.strip().strip('\n'), u'0')

    def test_queue_page_with_student(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.student.username, password=self.student_password))

        # get page
        response = client.get(reverse('courses.views.queue_page', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 403)

    def test_edit_course_information_with_student(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.student.username, password=self.student_password))

        # get page
        response = client.get(reverse('courses.views.edit_course_information'))
        self.assertEqual(response.status_code, 405)

        # post page
        response = client.post(reverse('courses.views.edit_course_information'),
                               {'course_id': self.course.id,
                                'course_information': 'course_information'})
        self.assertEqual(response.status_code, 403)

    def test_course_settings_with_student(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.student.username, password=self.student_password))

        # get page
        response = client.get(reverse('courses.views.course_settings', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 403)

        # post page
        response = client.post(reverse('courses.views.course_settings', kwargs={'course_id': self.course.id}),
                               {'group_1': '1'}, follow=True)
        self.assertEqual(response.status_code, 403)

    def test_change_visibility_hidden_tasks_with_student(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.student.username, password=self.student_password))

        # get page
        response = client.get(reverse('courses.views.change_visibility_hidden_tasks'))
        self.assertEqual(response.status_code, 405)

        # post page
        response = client.post(reverse('courses.views.change_visibility_hidden_tasks'),
                               {'course_id': self.course.id})
        self.assertEqual(response.status_code, 403)

    def test_set_course_mark_with_student(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.student.username, password=self.student_password))

        # get page
        # response = client.get(reverse('courses.views.set_course_mark'))
        # self.assertEqual(response.status_code, 403)

        mark_fields = [MarkField.objects.create(name='mark1'), MarkField.objects.create(name='mark2')]
        course_mark_system = CourseMarkSystem.objects.create(name='course_mark_system')
        course_mark_system.marks = mark_fields
        course_mark_system.save()
        self.course.mark_system = course_mark_system
        self.course.save()

        # get course page
        response = client.get(reverse('courses.views.gradebook', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container-fluid', recursive=False)

        # table results
        table = container.find('table', 'table-results')

        table_body_rows_cells = table.tbody('td')
        table_course_mark_form = table_body_rows_cells[4].form
        self.assertEqual(len(table_body_rows_cells), 5)
        self.assertEqual(table_body_rows_cells[4].span.string.strip().strip('\n'), u'--')
        self.assertIsNone(table_course_mark_form)

        # post page
        # response = client.post(reverse('courses.views.set_course_mark'),
        #                        {'course_id': self.course.id,
        #                         'group_id': self.group.id,
        #                         'student_id': self.student.id,
        #                         'mark_id': mark_fields[0].id})
        # self.assertEqual(response.status_code, 200)
        # self.assertEqual(response.content, '{"mark_id": 1, "mark": "mark1"}')

        # post page via teacher
        client.logout()
        self.assertTrue(client.login(username=self.teacher.username, password=self.teacher_password))
        response = client.post(reverse('courses.views.set_course_mark'),
                               {'course_id': self.course.id,
                                'group_id': self.group.id,
                                'student_id': self.student.id,
                                'mark_id': mark_fields[0].id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"mark_int": -1, "mark_id": 1, "mark": "mark1"}')

        # get course page
        self.assertTrue(client.login(username=self.student.username, password=self.student_password))
        response = client.get(reverse('courses.views.gradebook', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container-fluid', recursive=False)

        # table results
        table = container.find('table', 'table-results')

        table_body_rows_cells = table.tbody('td')
        table_course_mark_form = table_body_rows_cells[4].form
        self.assertEqual(len(table_body_rows_cells), 5)
        self.assertEqual(table_body_rows_cells[4].span.string.strip().strip('\n'), u'mark1')
        self.assertIsNone(table_course_mark_form)

    def test_set_task_mark_with_student(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.student.username, password=self.student_password))

        # get page
        # response = client.get(reverse('courses.views.set_task_mark'))
        # self.assertEqual(response.status_code, 403)

        task = Task.objects.create(title='task_title',
                                   course=self.course,
                                   score_max=10,
                                   type=Task.TYPE_SIMPLE)
        task.set_position_in_new_group()

        # get course page
        response = client.get(reverse('courses.views.gradebook', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container-fluid', recursive=False)

        # table results
        table = container.find('table', 'table-results')

        table_head = table.thead('th')[2]
        self.assertEqual(table_head.a.string.strip().strip('\n'), 'task_title')
        self.assertEqual(table_head.span.string.strip().strip('\n'), '10')

        table_body = table.tbody('td')[2]
        self.assertIsNotNone(table_body.find('div'))
        self.assertEqual(table_body.div.span.string.strip().strip('\n'), '0')
        self.assertIsNone(table_body.form)

        table_body_sum = table.tbody('td')[3]
        self.assertEqual(table_body_sum.span.string.strip().strip('\n'), '0')

        # post page
        # response = client.post(reverse('courses.views.set_task_mark'),
        #                        {'task_id': task.id,
        #                         'student_id': self.student.id,
        #                         'mark_max': task.score_max,
        #                         'mark_value': '3'})
        # self.assertEqual(response.status_code, 200)
        # self.assertEqual(response.content, '{"mark": 3.0}')

        # post page via teacher
        client.logout()
        self.assertTrue(client.login(username=self.teacher.username, password=self.teacher_password))
        response = client.post(reverse('courses.views.set_task_mark'),
                               {'task_id': task.id,
                                'student_id': self.student.id,
                                'mark_max': task.score_max,
                                'mark_value': '3'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"color": "' + IssueStatus.objects.get(pk=5).color + '", "mark": 3.0}')

        # get course page
        self.assertTrue(client.login(username=self.student.username, password=self.student_password))
        response = client.get(reverse('courses.views.gradebook', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)

        html = BeautifulSoup(response.content)
        container = html.body.find('div', 'container-fluid', recursive=False)

        # table results
        table = container.find('table', 'table-results')

        table_head = table.thead('th')[2]
        self.assertEqual(table_head.a.string.strip().strip('\n'), 'task_title')
        self.assertEqual(table_head.span.string.strip().strip('\n'), '10')

        table_body = table.tbody('td')[2]
        self.assertIsNotNone(table_body.find('div'))
        self.assertEqual(table_body.div.span.string.strip().strip('\n'), '3')
        self.assertIsNone(table_body.form)

        table_body_sum = table.tbody('td')[3]
        self.assertEqual(table_body_sum.span.string.strip().strip('\n'), '3.0')


class PythonTaskTest(TestCase):
    def setUp(self):
        User.objects.create_user(username="anytask")
        self.year = Year.objects.create(start_year=2016)
        self.group = Group(name="test_group", year=self.year)
        self.group.save()
        self.users = []
        for i in range(0, 10):
            user = User.objects.create_user(username='test_user{}'.format(i), password="password{}".format(i))
            user.first_name = "test_firstname{}".format(i)
            user.last_name = "test_lastname{}".format(i)
            user.save()
            self.users.append(user)
            self.group.students.add(user)

        self.teacher = User.objects.create_user(username='test_teacher', password='teacher')

        seminar_status = IssueStatus(name="seminar", tag=IssueStatus.STATUS_SEMINAR)
        seminar_status.save()
        issue_status_system = IssueStatusSystem()
        issue_status_system.name = "seminar"
        issue_status_system.save()
        issue_status_system.statuses.add(seminar_status)

        self.course = Course()
        self.course.name = 'python.task'
        self.course.is_active = True
        self.course.year = self.year
        self.course.save()
        self.course.teachers.add(self.teacher)
        self.course.groups.add(self.group)
        # course.mark_system = mark_system
        self.issue_status_system = issue_status_system
        self.course.is_python_task = True
        self.course.save()

        self.task = Task.objects.create(title='task_title', course=self.course, score_max=10)
        self.task2 = Task.objects.create(title='task2_title', course=self.course, score_max=10)
        self.task3 = Task.objects.create(title='task3_title', course=self.course, score_max=10)
        self.seminar = Task.objects.create(title='seminar_title', course=self.course, type=Task.TYPE_SEMINAR)
        self.subtask1 = Task.objects.create(
            title='subtask1_title', course=self.course, parent_task=self.seminar, score_max=10
        )
        self.subtask2 = Task.objects.create(
            title='subtask2_title', course=self.course, parent_task=self.seminar, score_max=10
        )

        self.task4_expired = Task.objects.create(title='task4_title', course=self.course, score_max=10)

    def test_list(self):
        client = self.client
        self.assertTrue(client.login(username=self.teacher.username, password="teacher"))
        response = client.get(reverse('courses.views.course_page', kwargs={'course_id': self.course.id}))
        content = str(response.content)
        self.assertIn("task_title", content)
        self.assertIn("seminar_title", content)
        self.assertIn("subtask1_title", content)
        self.assertIn("subtask2_title", content)

    def test_take_and_cancel_task(self):
        client = self.client
        user = self.users[0]
        self.assertTrue(client.login(username=user.username, password="password0"))
        response = client.get(reverse('courses.views.course_page', kwargs={'course_id': self.course.id}))
        self.assertNotContains(response, "{} {}".format(user.last_name, user.first_name))

        response = client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id, 'task_id': self.task.id}),
            follow=True)
        self.assertContains(response, "{} {}".format(user.last_name, user.first_name))

        response = client.get(
            reverse('courses.pythontask.cancel_task', kwargs={'course_id': self.course.id, 'task_id': self.task.id}),
            follow=True)
        self.assertNotContains(response, "{} {}".format(user.last_name, user.first_name))

    def test_take_and_cancel_subtask(self):
        client = self.client
        user = self.users[0]
        self.assertTrue(client.login(username=user.username, password="password0"))
        response = client.get(reverse('courses.views.course_page', kwargs={'course_id': self.course.id}))
        self.assertNotContains(response, "{} {}".format(user.last_name, user.first_name))

        response = client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id, 'task_id': self.subtask1.id}),
            follow=True)
        self.assertContains(response, "{} {}".format(user.last_name, user.first_name))

        response = client.get(
            reverse(
                'courses.pythontask.cancel_task',
                kwargs={'course_id': self.course.id, 'task_id': self.subtask1.id}
            ),
            follow=True
        )

        self.assertNotContains(response, "{} {}".format(user.last_name, user.first_name))

    def test_take_tasks_limit(self):
        client = self.client

        for i, user in enumerate(self.users[:8]):
            self.assertTrue(client.login(username=user, password="password{}".format(i)))
            response = client.get(reverse('courses.views.course_page', kwargs={'course_id': self.course.id}))
            self.assertNotContains(response, "{} {}".format(user.last_name, user.first_name))

            response = client.get(
                reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id, 'task_id': self.task.id}),
                follow=True)
            self.assertContains(response, "{} {}".format(user.last_name, user.first_name))

        user = self.users[9]
        self.assertTrue(client.login(username=user, password="password9"))
        response = client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id, 'task_id': self.task.id}),
            follow=True)
        self.assertNotContains(response, "{} {}".format(user.last_name, user.first_name))

    def test_take_subtasks_limit(self):
        client = self.client

        for i, user in enumerate(self.users[:8]):
            self.assertTrue(client.login(username=user, password="password{}".format(i)))
            response = client.get(reverse('courses.views.course_page', kwargs={'course_id': self.course.id}))
            self.assertNotContains(response, "{} {}".format(user.last_name, user.first_name))

            response = client.get(reverse('courses.pythontask.get_task',
                                          kwargs={'course_id': self.course.id, 'task_id': self.subtask1.id}),
                                  follow=True)
            self.assertContains(response, "{} {}".format(user.last_name, user.first_name))

        user = self.users[9]
        self.assertTrue(client.login(username=user, password="password9"))
        response = client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id, 'task_id': self.subtask1.id}),
            follow=True)
        self.assertNotIn("{} {}".format(user.last_name, user.first_name), response.content)

    def test_take_cant_take_tasks_from_one_subtask(self):
        client = self.client
        user = self.users[0]

        self.assertTrue(client.login(username=user.username, password="password0"))
        response = client.get(reverse('courses.views.course_page', kwargs={'course_id': self.course.id}))
        self.assertNotIn("{} {}".format(user.last_name, user.first_name), response.content)

        response = client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id, 'task_id': self.subtask1.id}),
            follow=True)
        self.assertContains(response, "{} {}".format(user.last_name, user.first_name), count=1)

        response = client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id, 'task_id': self.subtask2.id}),
            follow=True)
        self.assertContains(response, "{} {}".format(user.last_name, user.first_name), count=1)

    def set_mark(self, task, student, mark):
        issue, _ = Issue.objects.get_or_create(task_id=task.id, student_id=student.id)
        issue.mark = mark
        issue.save()

    def test_max_incomplete_constraint(self):
        client = self.client
        user = self.users[0]
        self.assertTrue(client.login(username=user.username, password='password0'))

        client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id,
                    'task_id': self.task.id}), follow=True)
        self.set_mark(self.task, user, 1.0)

        client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id,
                    'task_id': self.task3.id}), follow=True)
        self.set_mark(self.task3, user, 2.0)

        response = client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id,
                    'task_id': self.subtask1.id}), follow=True)

        self.assertContains(response, "{} {}".format(user.last_name, user.first_name), count=3)

        response = client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id,
                    'task_id': self.task2.id}), follow=True)
        self.assertContains(response, "{} {}".format(user.last_name, user.first_name), count=3)

        self.set_mark(self.task3, user, 10)
        response = client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id,
                    'task_id': self.task2.id}), follow=True)
        self.assertContains(response, "{} {}".format(user.last_name, user.first_name), count=4)

    def test_statistics(self):
        client = self.client
        user1 = self.users[0]
        user2 = self.users[1]

        self.assertTrue(client.login(username=user1.username, password='password0'))
        client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id,
                    'task_id': self.subtask1.id}), follow=True)
        client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id,
                    'task_id': self.task.id}), follow=True)

        self.assertTrue(client.login(username=user2.username, password='password1'))
        client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id,
                    'task_id': self.subtask2.id}), follow=True)
        client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id,
                    'task_id': self.task.id}), follow=True)

        self.assertTrue(client.login(username=self.teacher.username, password='teacher'))
        self.set_mark(self.task, user1, 1.5)
        self.set_mark(self.subtask1, user1, 2.3)
        self.set_mark(self.subtask2, user2, 1.0)

        self.assertTrue(client.login(username=user1.username, password='password0'))
        response = client.get(
            reverse('courses.views.view_statistic', kwargs={'course_id': self.course.id}), follow=True)
        self.assertContains(response, "1.5")
        self.assertContains(response, "2.3")
        self.assertContains(response, "1")
        self.assertContains(response, "3.8")

    def _test_set_detault_teacher__retake_task(self):
        client = self.client
        user = self.users[0]

        self.assertTrue(client.login(username=user.username, password="password0"))

        # cancel task
        client.get(reverse('courses.pythontask.cancel_task',
                           kwargs={'course_id': self.course.id, 'task_id': self.task.id}),
                   follow=True)

        # get task
        client.get(reverse('courses.pythontask.get_task',
                           kwargs={'course_id': self.course.id, 'task_id': self.task.id}),
                   follow=True)

        # create issue
        client.get(reverse('issues.views.get_or_create',
                           kwargs={'student_id': user.id, 'task_id': self.task.id}),
                   follow=True)

        # get task list
        client.get(reverse('courses.views.course_page',
                           kwargs={'course_id': self.course.id}),
                   follow=True)

    def test_set_detault_teacher(self):
        # check no teacher if default teacher not set
        self._test_set_detault_teacher__retake_task()
        issue = Issue.objects.get(task=self.task)
        self.assertIsNone(issue.responsible)

        # set default teacher
        default_teacher = DefaultTeacher(teacher=self.teacher, course=self.course, group=self.group)
        default_teacher.save()
        self._test_set_detault_teacher__retake_task()
        issue = Issue.objects.get(task=self.task)
        self.assertEqual(issue.responsible, self.teacher)

        # check default teacher will not be changed if its already set
        default_teacher.teacher = self.users[1]
        default_teacher.save()
        self._test_set_detault_teacher__retake_task()
        issue = Issue.objects.get(task=self.task)
        self.assertEqual(issue.responsible, self.teacher)

    def test_expired(self):
        client = self.client
        user = self.users[0]
        check_task_taken_expires_command = CheckTastTakenExpiresCommand()

        self.assertTrue(client.login(username=user.username, password="password0"))

        # get the task
        response = client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id,
                                                           'task_id': self.task4_expired.id}),
            follow=True)
        self.assertContains(response, "{} {}".format(user.last_name, user.first_name))

        # check its taken
        task_taken = TaskTaken.objects.get(task=self.task4_expired, user=user)
        self.assertEqual(task_taken.status, TaskTaken.STATUS_TAKEN)

        # just before the dedline
        task_taken.taken_time -= datetime.timedelta(days=settings.PYTHONTASK_MAX_DAYS_WITHOUT_SCORES + 1)
        task_taken.save()

        # cancel task
        response = client.get(reverse('courses.pythontask.cancel_task',
                                      kwargs={'course_id': self.course.id, 'task_id': self.task4_expired.id}),
                              follow=True)
        self.assertNotContains(response, "{} {}".format(user.last_name, user.first_name))
        task_taken = TaskTaken.objects.get(task=self.task4_expired, user=user)
        taken_time = task_taken.taken_time
        self.assertEqual(task_taken.status, TaskTaken.STATUS_CANCELLED)

        # get the task back
        response = client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id,
                                                           'task_id': self.task4_expired.id}),
            follow=True)
        self.assertContains(response, "{} {}".format(user.last_name, user.first_name))

        task_taken = TaskTaken.objects.get(task=self.task4_expired, user=user)
        self.assertEqual(task_taken.status, TaskTaken.STATUS_TAKEN)
        self.assertEqual(task_taken.taken_time, taken_time)

        # expire the task
        task_taken.taken_time -= datetime.timedelta(days=1)
        task_taken.save()

        check_task_taken_expires_command.check_course_task_taken_expires(self.course)
        check_task_taken_expires_command.check_blacklist_expires(self.course)
        task_taken = TaskTaken.objects.get(task=self.task4_expired, user=user)
        self.assertEqual(task_taken.status, TaskTaken.STATUS_BLACKLISTED)

        # check we cant task the task
        response = client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id,
                                                           'task_id': self.task4_expired.id}),
            follow=True)
        self.assertNotContains(response, "{} {}".format(user.last_name, user.first_name))

        # move a little bit in the past
        task_taken.taken_time -= datetime.timedelta(days=settings.PYTHONTASK_DAYS_DROP_FROM_BLACKLIST / 2)
        task_taken.save()

        # check we stil cant task the task
        response = client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id,
                                                           'task_id': self.task4_expired.id}),
            follow=True)
        self.assertNotContains(response, "{} {}".format(user.last_name, user.first_name))

        # drop from blacklist
        task_taken.taken_time -= datetime.timedelta(days=settings.PYTHONTASK_DAYS_DROP_FROM_BLACKLIST / 2)
        task_taken.save()

        check_task_taken_expires_command.check_course_task_taken_expires(self.course)
        check_task_taken_expires_command.check_blacklist_expires(self.course)
        task_taken = TaskTaken.objects.get(task=self.task4_expired, user=user)
        self.assertEqual(task_taken.status, TaskTaken.STATUS_DELETED)

        # check we can task the task again
        response = client.get(
            reverse('courses.pythontask.get_task', kwargs={'course_id': self.course.id,
                                                           'task_id': self.task4_expired.id}),
            follow=True)
        self.assertContains(response, "{} {}".format(user.last_name, user.first_name))
