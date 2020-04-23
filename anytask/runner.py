# from django.test.simple import DjangoTestSuiteRunner
from django.test.runner import DiscoverRunner as DjangoTestSuiteRunner
from django.conf import settings

EXCLUDED_APPS = getattr(settings, 'TEST_EXCLUDE', [])


class ExcludeAppsTestSuiteRunner(DjangoTestSuiteRunner):
    def build_suite(self, *args, **kwargs):
        suite = super(ExcludeAppsTestSuiteRunner, self).build_suite(*args, **kwargs)
        tests = []
        for case in suite:
            pkg = case.__class__.__module__.split('.')[1]
            if pkg not in EXCLUDED_APPS:
                tests.append(case)
        suite._tests = tests
        return suite
