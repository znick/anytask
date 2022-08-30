"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.urls import reverse

from schools.models import School


class IndexTest(TestCase):
    def test_schools_presence(self):
        """
        Test that active/archieved schools are present in
        active/archived indexes respectively and only there.
        """
        # Create data
        School.objects.create(
            name='active_school', link='active_school', is_active=True)
        School.objects.create(
            name='archived_school', link='archived_school', is_active=False)
        # Active index
        response = self.client.get(reverse('index.views.index'))
        self.assertQuerysetEqual(
            response.context['schools'],
            ['<School: active_school>']
        )
        # Archive index
        response = self.client.get(reverse('index.views.archive_index'))
        self.assertQuerysetEqual(
            response.context['schools'],
            ['<School: archived_school>']
        )

    def test_switch_lang(self):
        for lang in ('en', 'ru'):
            response = self.client.post(reverse('set_lang'), {'lang': lang})
            self.assertEqual(response.status_code, 200)

            response = self.client.get(reverse('get_lang'))
            self.assertEqual(response.content.decode("utf-8"), lang)

    def test_switch_wrong(self):
        response = self.client.get(reverse('get_lang'))
        current_lang = response.content

        # bad language
        response = self.client.post(reverse('set_lang'), {'lang': 'no_such_lang'})
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('get_lang'))
        self.assertEqual(response.content, current_lang)  # language not changed

        # bad request
        response = self.client.post(reverse('set_lang'), {'lang': ''})
        self.assertEqual(response.status_code, 400)

        response = self.client.get(reverse('get_lang'))
        self.assertEqual(response.content, current_lang)  # language not changed
