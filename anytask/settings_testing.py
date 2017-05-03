# -*- coding: utf-8 -*-

from settings import *

DEBUG = False

# SHAD admission settings
YA_FORMS_OAUTH = 'TEST_YA_FORMS_OAUTH'
YA_FORMS_FIELDS = {
    'last_name': 'field_1',
    'first_name': 'field_2',
    'middle_name': 'field_3',
    'email': 'field_4',
    'phone': 'field_5',
    'birth_date': 'field_6',
    'city_of_residence': 'field_7',
    'filial': 'field_8',
    'university': 'field_9',
    'university_text': 'field_10',
    'university_in_process': 'field_11',
    'university_class': 'field_12',
    'university_class_text': 'field_13',
    'university_department': 'field_14',
    'university_year_end': 'field_15',
}
YA_FORMS_FIELDS_ADDITIONAL = {
    'additional_info': ['field_16', 'field_17', 'field_18', 'field_19'],
}
ADMISSION_DATE_END = "10.05.17 15:00"
FILIAL_STATUSES = {}
ENROLLEE_STATUS = 1
CONTEST_URL = 'https://contest.yandex.ru/contest/'



