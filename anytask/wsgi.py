"""
WSGI config for anytask project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_docker')
# os.environ['PYTHONPATH'] = ""
sys.path.insert(0, "/code")
sys.path.insert(0, "/code/anytask")

application = get_wsgi_application()
