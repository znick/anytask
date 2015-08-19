#
# Regular cron jobs for the anytask package
#
# ТЫ БУДЕШЬ ОСТАВЛЯТЬ ПУСТУЮ СТРОКУ В КОНЦЕ ЭТОГО ФАЙЛА
#

MAILTO=gebetix@yandex-team.ru
HOME=/home/anytask/
SHELL=/bin/bash

0   2   *   *   *  anytask  cd /usr/share/python/anytask/lib/python2.7/site-packages/Anytask-0.0.0-py2.7.egg/anytask && /usr/share/python/anytask/bin/python manage.py cleanup
0   3   *   *   *  anytask  cd /usr/share/python/anytask/lib/python2.7/site-packages/Anytask-0.0.0-py2.7.egg/anytask && /usr/share/python/anytask/bin/python manage.py check_invite_expires
0   4   *   *   *  anytask  cd /usr/share/python/anytask/lib/python2.7/site-packages/Anytask-0.0.0-py2.7.egg/anytask && /usr/share/python/anytask/bin/python manage.py cleanupregistration
*/5 *   *   *   *  anytask  cd /usr/share/python/anytask/lib/python2.7/site-packages/Anytask-0.0.0-py2.7.egg/anytask && /usr/share/python/anytask/bin/python manage.py check_contest
*/5 *   *   *   *  anytask  cd /usr/share/python/anytask/lib/python2.7/site-packages/Anytask-0.0.0-py2.7.egg/anytask && /usr/share/python/anytask/bin/python manage.py send_notifications

