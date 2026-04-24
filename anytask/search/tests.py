# -*- coding: utf-8 -*-

import json

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from courses.models import Course
from groups.models import Group
from schools.models import School
from years.models import Year

import search.views


def make_user(username, first='', last='', email='', password='password', **profile_fields):
    user = User.objects.create_user(username=username, password=password,
                                    first_name=first, last_name=last, email=email)
    if profile_fields:
        profile = user.profile
        for k, v in profile_fields.items():
            setattr(profile, k, v)
        profile.save()
    return user


@override_settings(LANGUAGE_CODE='en-EN', LANGUAGES=(('en', 'English'),))
class SearchUsersTest(TestCase):
    def setUp(self):
        self.year = Year.objects.create(start_year=2024)

        self.school = School.objects.create(name='Test School', link='testschool')
        self.school2 = School.objects.create(name='Other School', link='otherschool')

        self.group = Group.objects.create(name='Group A', year=self.year)
        self.group2 = Group.objects.create(name='Group B', year=self.year)

        self.course = Course.objects.create(name='Algorithms', year=self.year)
        self.course.groups.set([self.group])
        self.school.courses.set([self.course])

        self.course2 = Course.objects.create(name='Math', year=self.year)
        self.course2.groups.set([self.group2])
        self.school2.courses.set([self.course2])

        self.searcher = make_user('searcher', first='Alice', last='Smith')
        self.group.students.add(self.searcher)

        self.peer = make_user('peer_user', first='Bob', last='Jones')
        self.group.students.add(self.peer)

        self.other_school_user = make_user('outsider', first='Carol', last='Brown')
        self.group2.students.add(self.other_school_user)

        self.teacher = make_user('teacher', first='Dave', last='Teacher')
        self.course.teachers.add(self.teacher)

        self.staff = User.objects.create_superuser('admin', 'admin@example.com', 'password')

    def _search_users(self, query, as_user, max_result=None):
        url = reverse(search.views.ajax_search_users)
        params = {'q': query}
        if max_result is not None:
            params['max'] = max_result
        self.client.force_login(as_user)
        return self.client.get(url, params)

    def test_unauthenticated_redirects(self):
        response = self.client.get(reverse(search.views.ajax_search_users), {'q': 'bob'})
        self.assertEqual(response.status_code, 302)

    def test_missing_q_returns_403(self):
        self.client.force_login(self.searcher)
        response = self.client.get(reverse(search.views.ajax_search_users))
        self.assertEqual(response.status_code, 403)

    def test_empty_query_returns_empty(self):
        response = self._search_users('', self.searcher)
        data = json.loads(response.content)
        self.assertEqual(data['result'], [])

    def test_find_peer_by_first_name(self):
        response = self._search_users('Bob', self.searcher)
        data = json.loads(response.content)
        usernames = [r['username'] for r in data['result']]
        self.assertIn('peer_user', usernames)

    def test_find_peer_by_last_name(self):
        response = self._search_users('Jones', self.searcher)
        data = json.loads(response.content)
        usernames = [r['username'] for r in data['result']]
        self.assertIn('peer_user', usernames)

    def test_find_peer_by_username(self):
        response = self._search_users('peer', self.searcher)
        data = json.loads(response.content)
        usernames = [r['username'] for r in data['result']]
        self.assertIn('peer_user', usernames)

    def test_find_peer_by_full_name(self):
        response = self._search_users('Bob Jones', self.searcher)
        data = json.loads(response.content)
        usernames = [r['username'] for r in data['result']]
        self.assertIn('peer_user', usernames)

    def test_find_peer_by_full_name_reversed(self):
        response = self._search_users('Jones Bob', self.searcher)
        data = json.loads(response.content)
        usernames = [r['username'] for r in data['result']]
        self.assertIn('peer_user', usernames)

    def test_case_insensitive_match(self):
        response = self._search_users('bob', self.searcher)
        data = json.loads(response.content)
        usernames = [r['username'] for r in data['result']]
        self.assertIn('peer_user', usernames)

    def test_partial_name_match(self):
        response = self._search_users('ob', self.searcher)
        data = json.loads(response.content)
        usernames = [r['username'] for r in data['result']]
        self.assertIn('peer_user', usernames)

    def test_self_excluded_from_results(self):
        response = self._search_users('Alice', self.searcher)
        data = json.loads(response.content)
        usernames = [r['username'] for r in data['result']]
        self.assertNotIn('searcher', usernames)

    def test_student_cannot_find_different_school_user(self):
        response = self._search_users('Carol', self.searcher)
        data = json.loads(response.content)
        usernames = [r['username'] for r in data['result']]
        self.assertNotIn('outsider', usernames)

    def test_student_cannot_search_by_email(self):
        peer_profile = self.peer.profile
        peer_profile.ya_passport_email = 'bob.secret@yandex.ru'
        peer_profile.save()
        response = self._search_users('bob.secret', self.searcher)
        data = json.loads(response.content)
        self.assertEqual(data['result'], [])

    def test_teacher_can_search_by_ya_contest_login(self):
        self.peer.profile.ya_contest_login = 'bob_contest'
        self.peer.profile.save()
        response = self._search_users('bob_contest', self.teacher)
        data = json.loads(response.content)
        usernames = [r['username'] for r in data['result']]
        self.assertIn('peer_user', usernames)

    def test_teacher_can_search_by_email(self):
        self.peer.email = 'bob@example.com'
        self.peer.save()
        response = self._search_users('bob@example', self.teacher)
        data = json.loads(response.content)
        usernames = [r['username'] for r in data['result']]
        self.assertIn('peer_user', usernames)

    def test_staff_finds_any_user(self):
        response = self._search_users('Carol', self.staff)
        data = json.loads(response.content)
        usernames = [r['username'] for r in data['result']]
        self.assertIn('outsider', usernames)

    def test_max_result_limits_and_is_limited_flag(self):
        for i in range(5):
            u = make_user(f'extra_peer_{i}', first='Bob', last=f'Extra{i}')
            self.group.students.add(u)

        response = self._search_users('Bob', self.staff, max_result=3)
        data = json.loads(response.content)
        self.assertLessEqual(len(data['result']), 3)
        self.assertTrue(data['is_limited'])

    def test_is_limited_false_when_few_results(self):
        response = self._search_users('Dave', self.staff, max_result=10)
        data = json.loads(response.content)
        self.assertFalse(data['is_limited'])

    def test_result_contains_expected_fields(self):
        response = self._search_users('Bob', self.staff)
        data = json.loads(response.content)
        self.assertTrue(len(data['result']) > 0)
        r = data['result'][0]
        for field in ('fullname', 'username', 'url', 'avatar', 'email', 'id', 'statuses'):
            self.assertIn(field, r)


@override_settings(LANGUAGE_CODE='en-EN', LANGUAGES=(('en', 'English'),))
class SearchCoursesTest(TestCase):
    def setUp(self):
        self.year = Year.objects.create(start_year=2024)

        self.school = School.objects.create(name='Test School', link='testschool')

        self.group = Group.objects.create(name='Group A', year=self.year)

        self.course_active = Course.objects.create(name='Algorithms', year=self.year, is_active=True)
        self.course_active.groups.set([self.group])
        self.school.courses.set([self.course_active])

        self.course_inactive = Course.objects.create(name='Ancient History', year=self.year, is_active=False)
        self.course_inactive.groups.set([self.group])

        self.unrelated_course = Course.objects.create(name='Algorithms Advanced', year=self.year)

        self.student = make_user('student')
        self.group.students.add(self.student)

        self.teacher = make_user('teacher')
        self.course_active.teachers.add(self.teacher)

        self.staff = User.objects.create_superuser('admin', 'admin@example.com', 'password')

    def _search_courses(self, query, as_user, max_result=None):
        url = reverse(search.views.ajax_search_courses)
        params = {'q': query}
        if max_result is not None:
            params['max'] = max_result
        self.client.force_login(as_user)
        return self.client.get(url, params)

    def test_unauthenticated_redirects(self):
        response = self.client.get(reverse(search.views.ajax_search_courses), {'q': 'algo'})
        self.assertEqual(response.status_code, 302)

    def test_missing_q_returns_403(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse(search.views.ajax_search_courses))
        self.assertEqual(response.status_code, 403)

    def test_empty_query_returns_empty(self):
        response = self._search_courses('', self.student)
        data = json.loads(response.content)
        self.assertEqual(data['result'], [])

    def test_student_finds_own_course(self):
        response = self._search_courses('Algo', self.student)
        data = json.loads(response.content)
        names = [r['name'] for r in data['result']]
        self.assertIn('Algorithms', names)

    def test_student_cannot_find_unrelated_course(self):
        response = self._search_courses('Advanced', self.student)
        data = json.loads(response.content)
        names = [r['name'] for r in data['result']]
        self.assertNotIn('Algorithms Advanced', names)

    def test_teacher_finds_own_course(self):
        response = self._search_courses('Algo', self.teacher)
        data = json.loads(response.content)
        names = [r['name'] for r in data['result']]
        self.assertIn('Algorithms', names)

    def test_staff_finds_all_courses(self):
        response = self._search_courses('Algo', self.staff)
        data = json.loads(response.content)
        names = [r['name'] for r in data['result']]
        self.assertIn('Algorithms', names)
        self.assertIn('Algorithms Advanced', names)

    def test_case_insensitive_match(self):
        response = self._search_courses('algo', self.staff)
        data = json.loads(response.content)
        names = [r['name'] for r in data['result']]
        self.assertIn('Algorithms', names)

    def test_partial_name_match(self):
        response = self._search_courses('ncient', self.student)
        data = json.loads(response.content)
        names = [r['name'] for r in data['result']]
        self.assertIn('Ancient History', names)

    def test_active_courses_ordered_first(self):
        response = self._search_courses('a', self.student)
        data = json.loads(response.content)
        results = data['result']
        active_flags = [r['is_active'] for r in results]
        if len(active_flags) > 1:
            self.assertTrue(active_flags[0] >= active_flags[-1])

    def test_result_contains_expected_fields(self):
        response = self._search_courses('Algo', self.staff)
        data = json.loads(response.content)
        self.assertTrue(len(data['result']) > 0)
        r = data['result'][0]
        for field in ('name', 'year', 'url', 'schools', 'is_active'):
            self.assertIn(field, r)

    def test_max_result_limits_and_is_limited_flag(self):
        for i in range(5):
            Course.objects.create(name=f'Algorithms Part {i}', year=self.year)

        response = self._search_courses('Algo', self.staff, max_result=3)
        data = json.loads(response.content)
        self.assertLessEqual(len(data['result']), 3)
        self.assertTrue(data['is_limited'])

    def test_search_page_renders(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse(search.views.search_page), {'q': 'Algo'})
        self.assertEqual(response.status_code, 200)
