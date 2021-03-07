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
