"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse


class TestResponse(TestCase):
    def setUp(self):
        self.user_password = 'password1'
        self.user = User.objects.create_user(username='user',
                                             password=self.user_password)

    def test_get_page_anonymously(self):
        client = self.client

        # get blog page
        response = client.get(reverse('blog.views.blog_page'))
        self.assertEqual(response.status_code, 200)

    def test_get_page_via_user(self):
        client = self.client

        # login
        self.assertTrue(client.login(username=self.user.username, password=self.user_password))

        # get blog page
        response = client.get(reverse('blog.views.blog_page'))
        self.assertEqual(response.status_code, 200)

