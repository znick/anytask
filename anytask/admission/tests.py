# -*- coding: utf-8 -*-

from django.test import TestCase
from mock import patch

from django.core.urlresolvers import reverse
from django.conf import settings

from users.model_user_status import UserStatus
from admission.models import AdmissionRegistrationProfile
from django.contrib.auth.models import User

import json
import datetime

import admission.views


class ViewsTest(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.enrollee_status = UserStatus.objects.create(name='enrollee_status', type=UserStatus.TYPE_ADMISSION)
        settings.ENROLLEE_STATUS = self.enrollee_status.id

        self.filial_name = 'filial'
        self.filial_status = UserStatus.objects.create(name=self.filial_name, type=UserStatus.TYPE_FILIAL)
        settings.FILIAL_STATUSES = {
            self.filial_name: self.filial_status.id
        }

        self.contest_id = '1'

    @patch('admission.views.contest_register')
    def test_register_activate(self, mock_contest_register):
        client = self.client

        test_header = {
            'HTTP_OAUTH': settings.YA_FORMS_OAUTH,
            'HTTP_LOGIN': 'login',
            'HTTP_UID': '123',
            'HTTP_EMAIL': 'email@ya.ru',
        }
        test_birth_date = datetime.date(2000, 1, 1)
        test_data = {
            'last_name': 'last_name',
            'first_name': 'first_name',
            'middle_name': 'middle_name',
            'email': 'email@1.ru',
            'phone': 'phone',
            'birth_date': u'1 января 2000 г.',
            'city_of_residence': 'city_of_residence',
            'filial': self.filial_name,
            'university': 'university',
            'university_text': 'university_text',
            'university_in_process': u'Да',
            'university_class': 'university_class',
            'university_class_text': 'university_class_text',
            'university_department': 'university_department',
            'university_year_end': 'university_year_end',
        }
        test_data_additional = {
            'field_16': 'field_16',
            'field_17': 'field_17',
            'field_18': 'field_18',
            'field_19': 'field_19',
        }
        post_data = {
            u'noop': [u'content'],
            u'field_1': [u'{"question": {"id": 1, "label": {"ru": "q1"}}, "value": "' + test_data['last_name'] + u'"}'],
            u'field_2': [
                u'{"question": {"id": 2, "label": {"ru": "q2"}}, "value": "' + test_data['first_name'] + u'"}'],
            u'field_3': [
                u'{"question": {"id": 3, "label": {"ru": "q3"}}, "value": "' + test_data['middle_name'] + u'"}'],
            u'field_4': [u'{"question": {"id": 4, "label": {"ru": "q4"}}, "value": "' + test_data['email'] + u'"}'],
            u'field_5': [u'{"question": {"id": 5, "label": {"ru": "q5"}}, "value": "' + test_data['phone'] + u'"}'],
            u'field_6': [
                u'{"question": {"id": 6, "label": {"ru": "q6"}}, "value": "' + test_data['birth_date'] + u'"}'],
            u'field_7': [
                u'{"question": {"id": 7, "label": {"ru": "q7"}}, "value": "' + test_data['city_of_residence'] + u'"}'],
            u'field_8': [u'{"question": {"id": 8, "label": {"ru": "q8"}}, "value": "' + test_data['filial'] + u'"}'],
            u'field_9': [
                u'{"question": {"id": 9, "label": {"ru": "q9"}}, "value": "' + test_data['university'] + u'"}'],
            u'field_10': [
                u'{"question": {"id": 10, "label": {"ru": "q10"}}, "value": "' + test_data['university_text'] + u'"}'],
            u'field_11': [u'{"question": {"id": 11, "label": {"ru": "q11"}}, "value": "' + test_data[
                'university_in_process'] + u'"}'],
            u'field_12': [
                u'{"question": {"id": 12, "label": {"ru": "q12"}}, "value": "' + test_data['university_class'] + u'"}'],
            u'field_13': [u'{"question": {"id": 13, "label": {"ru": "q13"}}, "value": "' + test_data[
                'university_class_text'] + u'"}'],
            u'field_14': [u'{"question": {"id": 14, "label": {"ru": "q14"}}, "value": "' + test_data[
                'university_department'] + u'"}'],
            u'field_15': [u'{"question": {"id": 15, "label": {"ru": "q15"}}, "value": "' + test_data[
                'university_year_end'] + u'"}'],
            u'field_16': [u'{"question": {"id": 16, "label": {"ru": "q16"}}, "value": "' + test_data_additional[
                'field_16'] + u'"}'],
            u'field_17': [u'{"question": {"id": 17, "label": {"ru": "q17"}}, "value": "' + test_data_additional[
                'field_17'] + u'"}'],
            u'field_18': [u'{"question": {"id": 18, "label": {"ru": "q18"}}, "value": "' + test_data_additional[
                'field_18'] + u'"}'],
            u'field_19': [u'{"question": {"id": 19, "label": {"ru": "q19"}}, "value": "' + test_data_additional[
                'field_19'] + u'"}'],
        }

        # get register
        response = client.get(reverse(admission.views.register), post_data, **test_header)
        self.assertEqual(response.status_code, 405)

        # post register without header
        response = client.post(reverse(admission.views.register), post_data)
        self.assertEqual(response.status_code, 403)

        # post register
        response = client.post(reverse(admission.views.register), post_data, **test_header)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")

        registration_profile = AdmissionRegistrationProfile.objects.all()
        self.assertEqual(len(registration_profile), 1)

        registration_profile = registration_profile[0]
        user_info = {
            'username': test_header['HTTP_LOGIN'],
            'uid': test_header['HTTP_UID'],
            'ya_email': test_header['HTTP_EMAIL'],
            'is_updating': False,
            'additional_info': '',
        }
        user_info.update(test_data)
        loaded_info = json.loads(registration_profile.user_info)
        loaded_info['additional_info'] = ''
        self.assertDictEqual(user_info, loaded_info)
        self.assertFalse(registration_profile.is_updating)

        user = registration_profile.user
        self.assertEqual(user.username, test_header['HTTP_LOGIN'])
        self.assertEqual(user.email, test_data['email'])
        self.assertFalse(user.is_active)
        self.assertEqual(user.last_name, test_data['last_name'])
        self.assertEqual(user.first_name, test_data['first_name'])

        user_profile = user.profile
        self.assertEqual(user_profile.middle_name, test_data['middle_name'])
        self.assertEqual(user_profile.birth_date, test_birth_date)
        self.assertEqual(user_profile.phone, test_data['phone'])
        self.assertEqual(user_profile.city_of_residence, test_data['city_of_residence'])
        self.assertEqual(user_profile.university, test_data['university'])
        self.assertTrue(user_profile.university_in_process)
        self.assertEqual(user_profile.university_class, test_data['university_class'])
        self.assertEqual(user_profile.university_department, test_data['university_department'])
        self.assertEqual(user_profile.university_year_end, test_data['university_year_end'])
        self.assertEqual(user_profile.ya_contest_uid, test_header['HTTP_UID'])
        self.assertEqual(user_profile.ya_contest_login, test_header['HTTP_LOGIN'])
        self.assertEqual(user_profile.ya_passport_uid, test_header['HTTP_UID'])
        self.assertEqual(user_profile.ya_passport_email, test_header['HTTP_EMAIL'])
        self.assertEqual(user_profile.ya_passport_login, test_header['HTTP_LOGIN'])

        user_statuses = user_profile.user_status.all()
        self.assertEqual(len(user_statuses), 2)
        user_status_filial = user_statuses.filter(type=UserStatus.TYPE_FILIAL)
        self.assertEqual(len(user_status_filial), 1)
        self.assertEqual(user_status_filial[0], self.filial_status)
        user_status_admission = user_statuses.filter(type=UserStatus.TYPE_ADMISSION)
        self.assertEqual(len(user_status_admission), 1)
        self.assertEqual(user_status_admission[0], self.enrollee_status)

        activation_key = registration_profile.activation_key

        # post activate
        mock_contest_register.return_value = self.contest_id
        response = client.post(reverse(admission.views.activate,
                                       kwargs={'activation_key': activation_key}))
        self.assertEqual(response.status_code, 405)

        # get activate with wrong key
        mock_contest_register.return_value = self.contest_id
        response = client.get(reverse(admission.views.activate, kwargs={'activation_key': '1'}))
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(id=user.id)
        self.assertFalse(user.is_active)
        registration_profile = AdmissionRegistrationProfile.objects.get(id=registration_profile.id)
        self.assertEqual(registration_profile.activation_key, activation_key)

        # get activate
        mock_contest_register.return_value = self.contest_id
        response = client.get(reverse(admission.views.activate,
                                      kwargs={'activation_key': activation_key}))
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], settings.CONTEST_URL + 'contest/' + self.contest_id)

        user = User.objects.get(id=user.id)
        self.assertTrue(user.is_active)
        registration_profile = AdmissionRegistrationProfile.objects.get(id=registration_profile.id)
        self.assertEqual(registration_profile.activation_key, AdmissionRegistrationProfile.ACTIVATED)
        self.assertEqual(registration_profile.old_activation_key, activation_key)
