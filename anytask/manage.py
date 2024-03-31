#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import locale
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
locale.setlocale(locale.LC_ALL, '')

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anytask.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

# To skip test_site_profile_not_available from django.contrib.auth.tests.models.ProfileTestCase
# see https://code.djangoproject.com/ticket/17966
sys.modules['django.contrib.auth.tests'] = None

if __name__ == '__main__':
    main()
