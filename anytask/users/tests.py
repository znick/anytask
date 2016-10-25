# encoding: utf-8


from django.test import TestCase
from django.contrib.auth.models import User


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
        self.assertContains(response, u"Логин / E-mail")
        self.assertContains(response, u"Пароль")

    def test_register_form(self):
        client = self.client
        response = client.get('/accounts/register/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/registration_form.html')

        self.assertContains(response, u"Логин")
        self.assertContains(response, u"Адрес электронной почты")

    def test_login_user__username(self):
        client = self.client

        form_data = {"username" : u"test_user0",
                     "password" : u"qwer0"}

        response = client.post('/accounts/login/', form_data)
        self.assertEqual(response.status_code, 302)

    def test_login_user__email(self):
        client = self.client

        form_data = {"username" : u"test_user0@example.com",
                     "password" : u"qwer0"}

        response = client.post('/accounts/login/', form_data)
        self.assertEqual(response.status_code, 302)

    def test_login_user__bad_login(self):
        client = self.client

        form_data = {"username" : u"login",
                     "password" : u"qwer0"}

        response = client.post('/accounts/login/', form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, u"Пожалуйста, введите верные имя пользователя и пароль. Помните, оба поля чувствительны к регистру.")

    def test_login_user__bad_password(self):
        client = self.client

        form_data = {"username" : u"test_user0",
                     "password" : u"qwerqwer"}

        response = client.post('/accounts/login/', form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, u"Пожалуйста, введите верные имя пользователя и пароль. Помните, оба поля чувствительны к регистру.")

    def test_login_user__bad_email(self):
        client = self.client

        form_data = {"username" : u"test_user1@example.com",
                     "password" : u"qwer0"}

        response = client.post('/accounts/login/', form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, u"Пожалуйста, введите верные имя пользователя и пароль. Помните, оба поля чувствительны к регистру.")

    def test_register_user(self):
        client = self.client

        form_data = {"username" : u"test_user1",
                     "email" : u"test_user_00@example.com",
                    "first_name" : u"Иван",
                    "last_name" : u"Иванов",
                     "password1" : u"qwer1",
                     "password2" : u"qwer1"}

        response = client.post('/accounts/register/', form_data)
        self.assertEqual(response.status_code, 302)

        user = User.objects.get(username="test_user1")
        self.assert_(user)
        self.assertFalse(user.is_active)

        user.is_active = True
        user.save()

        self.assertTrue(client.login(username = "test_user1", password="qwer1"))

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
        self.assertFormError(response, 'form', 'email', u"This email address is already in use. Please supply a different email address.")

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
