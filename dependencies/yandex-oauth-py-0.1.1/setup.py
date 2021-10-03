#!/usr/bin/env python

import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.version_info < (2,5):
    raise NotImplementedError("Sorry, you need at least Python 2.5 or Python 3.x to use yandex-oauth.")


setup(name='yandex-oauth-py',
      version='0.1.1',
      description='Package for working with Yandex OAuth https://tech.yandex.ru/oauth/',
      url='https://bitbucket.org/wa_pis/yandex-oauth-py/oauth',
      author='Anton Grudin',
      author_email='onepis2word@gmail.com',
      license='MIT',
      py_modules=['yandex_oauth'],
      keywords='yandex oauth python',
      install_requires=[
          'requests',
      ],
      test_suite='tests',
      zip_safe=False)
