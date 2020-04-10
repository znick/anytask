import os
import sys

activate_this = os.path.join("/usr/share/python/anytask", "bin/activate_this.py")
open(activate_this)
execfile(activate_this, dict(__file__=activate_this))

os.environ['DJANGO_SETTINGS_MODULE'] = "anytask.settings_production"
os.environ['PYTHON_EGG_CACHE'] = "/tmp/anytask_egg_cache"
os.environ['HOME'] = "/usr/share/python/anytask/lib/python2.7/site-packages/Anytask-0.0.0-py2.7.egg/anytask"
os.environ['PYTHONPATH'] = '/usr/share/python/anytask/lib/python2.7/site-packages/Anytask-0.0.0-py2.7.egg/anytask:/usr/share/python/anytask/lib/python2.7/site-packages/Anytask-0.0.0-py2.7.egg:' + os.environ.get('PYTHONPATH', '')

sys.path = ['/usr/share/python/anytask/lib/python2.7/site-packages/Anytask-0.0.0-py2.7.egg/anytask', '/usr/share/python/anytask/lib/python2.7/site-packages/Anytask-0.0.0-py2.7.egg'] + sys.path

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
