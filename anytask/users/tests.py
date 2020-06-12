# encoding: utf-8

from django.test import TestCase
from django.contrib.auth.models import User

from schools.models import School
from years.models import Year
from courses.models import Course
from groups.models import Group

from django.core.urlresolvers import reverse


class UserLoginTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test_user0", email="test_user0@example.com", password="qwer0")
        self.user.is_active = True
        self.user.first_name = u"Иван"
        self.user.last_name = u"Кузнецов"

    def test_login_form(self):
        client = self.client
        response = client.get('/accounts/login/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

        self.assertContains(response, "Логин / E-mail")
        self.assertContains(response, "Пароль")

    def test_register_form(self):
        client = self.client
        response = client.get('/accounts/register/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/registration_form.html')
        self.assertContains(response, "Логин", html=True)
        self.assertContains(response, "E-mail", html=True)

    def test_login_user__username(self):
        client = self.client

        form_data = {"username": u"test_user0",
                     "password": u"qwer0"}

        response = client.post('/accounts/login/', form_data)
        self.assertEqual(response.status_code, 302)

    def test_login_user__email(self):
        client = self.client

        form_data = {"username": u"test_user0@example.com",
                     "password": u"qwer0"}

        response = client.post('/accounts/login/', form_data)
        self.assertEqual(response.status_code, 302)

    def test_login_user__bad_login(self):
        client = self.client

        form_data = {"username": u"login",
                     "password": u"qwer0"}

        response = client.post('/accounts/login/', form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Пожалуйста, введите верные имя пользователя / адрес электронной почты  и пароль.", html=True
        )

    def test_login_user__bad_password(self):
        client = self.client

        form_data = {"username": u"test_user0",
                     "password": u"qwerqwer"}

        response = client.post('/accounts/login/', form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Пожалуйста, введите верные имя пользователя / адрес электронной почты  и пароль.", html=True
        )

    def test_login_user__bad_email(self):
        client = self.client

        form_data = {"username": u"test_user1@example.com",
                     "password": u"qwer0"}

        response = client.post('/accounts/login/', form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Пожалуйста, введите верные имя пользователя / адрес электронной почты и пароль.".encode('utf8')
        )

    def test_register_user(self):
        client = self.client

        form_data = {"username": u"test_user1",
                     "email": u"test_user_00@example.com",
                     "first_name": u"Иван",
                     "last_name": u"Иванов",
                     "password1": u"qwer1",
                     "password2": u"qwer1"}

        response = client.post('/accounts/register/', form_data)
        self.assertEqual(response.status_code, 302)

        user = User.objects.get(username="test_user1")
        self.assert_(user)
        self.assertFalse(user.is_active)

        user.is_active = True
        user.save()

        self.assertTrue(client.login(username="test_user1", password="qwer1"))

    def test_register_user__login_already_exists(self):
        client = self.client

        form_data = {"username": u"test_user0",
                     "email": u"test_user_00@example.com",
                     "first_name": u"Иван",
                     "last_name": u"Иванов",
                     "password1": u"qwer1",
                     "password2": u"qwer1"}

        response = client.post('/accounts/register/', form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', u"Пользователь с таким именем уже существует.")

    def test_register_user__email_already_exists(self):
        client = self.client

        form_data = {"username": u"test_user1",
                     "email": u"test_user0@example.com",
                     "first_name": u"Иван",
                     "last_name": u"Иванов",
                     "password1": u"qwer1",
                     "password2": u"qwer1"}

        response = client.post('/accounts/register/', form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email',
                             "This email address is already in use. Please supply a different email address.")

    def test_register_user__wrong_passwords(self):
        client = self.client

        form_data = {"username": u"test_user0",
                     "email": u"test_user_00@example.com",
                     "first_name": u"Иван",
                     "last_name": u"Иванов",
                     "password1": u"qwer1",
                     "password2": u"qwer2"}

        response = client.post('/accounts/register/', form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, u"Два поля с паролями не совпадают.")


class UserProfileAccess(TestCase):
    def setUp(self):
        self.password = 'password'

        self.teacher_1_course_1 = User.objects.create_user(username='teacher_1_course_1', password=self.password)
        self.teacher_2_course_1 = User.objects.create_user(username='teacher_2_course_1', password=self.password)
        self.teacher_1_course_2 = User.objects.create_user(username='teacher_1_course_2', password=self.password)
        self.student_1_group_1 = User.objects.create_user(username='student_1_group_1', password=self.password)
        self.student_2_group_1 = User.objects.create_user(username='student_2_group_1', password=self.password)
        self.student_1_group_2 = User.objects.create_user(username='student_1_group_2', password=self.password)
        self.student_1_group_3 = User.objects.create_user(username='student_1_group_3', password=self.password)

        self.user_staff = User.objects.create_user(username='user_staff', password=self.password)
        self.user_staff.is_staff = True
        self.user_staff.save()

        self.year = Year.objects.create(start_year=2016)

        self.group_1 = Group.objects.create(name='group_1', year=self.year)
        self.group_1.students = [self.student_1_group_1, self.student_2_group_1]

        self.group_2 = Group.objects.create(name='group_2', year=self.year)
        self.group_2.students = [self.student_1_group_2]

        self.group_3 = Group.objects.create(name='group_3', year=self.year)
        self.group_3.students = [self.student_1_group_3]

        self.course_1 = Course.objects.create(name='course_1', year=self.year)
        self.course_1.groups = [self.group_1, self.group_2]
        self.course_1.teachers = [self.teacher_1_course_1, self.teacher_2_course_1]

        self.course_2 = Course.objects.create(name='course_2', year=self.year)
        self.course_2.groups = [self.group_3]
        self.course_2.teachers = [self.teacher_1_course_2]

        self.school_1 = School.objects.create(name='school_1', link='school_1')

        self.school_2 = School.objects.create(name='school_2', link='school_2')

    def test_user_profile_access_anonymously(self):
        client = self.client

        # get page
        response = client.get(self.teacher_1_course_1.get_absolute_url())
        self.assertRedirects(response, "/accounts/login/?next=" + self.teacher_1_course_1.get_absolute_url(),
                             status_code=302)
        self.assertEqual(response.status_code, 302)

    def check_access(self, access_result):
        client = self.client
        result_index = 0

        # 0
        # get teacher_1_course_1 page
        response = client.get(reverse('users.views.profile', kwargs={'username': self.teacher_1_course_1.username}))
        self.assertEqual(response.status_code, access_result[result_index])
        result_index += 1

        # 1
        # get teacher_2_course_1 page
        response = client.get(reverse('users.views.profile', kwargs={'username': self.teacher_2_course_1.username}))
        self.assertEqual(response.status_code, access_result[result_index])
        result_index += 1

        # 2
        # get teacher_1_course_2 page
        response = client.get(reverse('users.views.profile', kwargs={'username': self.teacher_1_course_2.username}))
        self.assertEqual(response.status_code, access_result[result_index])
        result_index += 1

        # 3
        # get student_1_group_1 page
        response = client.get(reverse('users.views.profile', kwargs={'username': self.student_1_group_1.username}))
        self.assertEqual(response.status_code, access_result[result_index])
        result_index += 1

        # 4
        # get student_2_group_1 page
        response = client.get(reverse('users.views.profile', kwargs={'username': self.student_2_group_1.username}))
        self.assertEqual(response.status_code, access_result[result_index])
        result_index += 1

        # 5
        # get student_1_group_2 page
        response = client.get(reverse('users.views.profile', kwargs={'username': self.student_1_group_2.username}))
        self.assertEqual(response.status_code, access_result[result_index])
        result_index += 1

        # 6
        # get student_1_group_3 page
        response = client.get(reverse('users.views.profile', kwargs={'username': self.student_1_group_3.username}))
        self.assertEqual(response.status_code, access_result[result_index])
        result_index += 1

        # 7
        # get user_staff
        response = client.get(reverse('users.views.profile', kwargs={'username': self.user_staff.username}))
        self.assertEqual(response.status_code, access_result[result_index])
        result_index += 1

    def check_access_by_school(self,
                               user,
                               access_result_no_school,
                               access_result_one_school,
                               access_result_different_school):
        client = self.client

        # login
        self.assertTrue(client.login(username=user.username, password=self.password))

        # not in school
        self.check_access(access_result_no_school)

        # not in one school
        self.school_1.courses = [self.course_1, self.course_2]
        self.check_access(access_result_one_school)

        # not in different schools
        self.school_1.courses = [self.course_1]
        self.school_2.courses = [self.course_2]
        self.check_access(access_result_different_school)

    def test_user_profile_access_teacher_1_course_1(self):

        self.check_access_by_school(self.teacher_1_course_1,
                                    [
                                        200,  # teacher_1_course_1
                                        200,  # teacher_2_course_1
                                        403,  # teacher_1_course_2
                                        200,  # student_1_group_1
                                        200,  # student_2_group_1
                                        200,  # student_2_group_1
                                        403,  # student_1_group_3
                                        403,  # user_staff
                                    ],
                                    [
                                        200,  # teacher_1_course_1
                                        200,  # teacher_2_course_1
                                        200,  # teacher_1_course_2
                                        200,  # student_1_group_1
                                        200,  # student_2_group_1
                                        200,  # student_2_group_1
                                        200,  # student_1_group_3
                                        403,  # user_staff
                                    ],
                                    [
                                        200,  # teacher_1_course_1
                                        200,  # teacher_2_course_1
                                        403,  # teacher_1_course_2
                                        200,  # student_1_group_1
                                        200,  # student_2_group_1
                                        200,  # student_2_group_1
                                        403,  # student_1_group_3
                                        403,  # user_staff
                                    ])

    def test_user_profile_access_student_1_group_1(self):

        self.check_access_by_school(self.student_1_group_1,
                                    [
                                        200,  # teacher_1_course_1
                                        200,  # teacher_2_course_1
                                        403,  # teacher_1_course_2
                                        200,  # student_1_group_1
                                        200,  # student_2_group_1
                                        200,  # student_2_group_1
                                        403,  # student_1_group_3
                                        403,  # user_staff
                                    ],
                                    [
                                        200,  # teacher_1_course_1
                                        200,  # teacher_2_course_1
                                        200,  # teacher_1_course_2
                                        200,  # student_1_group_1
                                        200,  # student_2_group_1
                                        200,  # student_2_group_1
                                        200,  # student_1_group_3
                                        403,  # user_staff
                                    ],
                                    [
                                        200,  # teacher_1_course_1
                                        200,  # teacher_2_course_1
                                        403,  # teacher_1_course_2
                                        200,  # student_1_group_1
                                        200,  # student_2_group_1
                                        200,  # student_2_group_1
                                        403,  # student_1_group_3
                                        403,  # user_staff
                                    ])

    def test_user_profile_access_user_staff(self):

        self.check_access_by_school(self.user_staff,
                                    [
                                        200,  # teacher_1_course_1
                                        200,  # teacher_2_course_1
                                        200,  # teacher_1_course_2
                                        200,  # student_1_group_1
                                        200,  # student_2_group_1
                                        200,  # student_2_group_1
                                        200,  # student_1_group_3
                                        200,  # user_staff
                                    ],
                                    [
                                        200,  # teacher_1_course_1
                                        200,  # teacher_2_course_1
                                        200,  # teacher_1_course_2
                                        200,  # student_1_group_1
                                        200,  # student_2_group_1
                                        200,  # student_2_group_1
                                        200,  # student_1_group_3
                                        200,  # user_staff
                                    ],
                                    [
                                        200,  # teacher_1_course_1
                                        200,  # teacher_2_course_1
                                        200,  # teacher_1_course_2
                                        200,  # student_1_group_1
                                        200,  # student_2_group_1
                                        200,  # student_2_group_1
                                        200,  # student_1_group_3
                                        200,  # user_staff
                                    ])
