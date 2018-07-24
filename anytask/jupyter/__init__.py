from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


if not hasattr(settings, 'JUPYTER_NBGRADER_API_URL'):
    raise ImproperlyConfigured('The JUPYTER_NBGRADER_API_URL setting is required.')

# if not hasattr(settings, 'JUPYTER_NBGRADER_AUTH_TOKEN'):
#     raise ImproperlyConfigured('The JUPYTER_NBGRADER_AUTH_TOKEN setting is required.')
