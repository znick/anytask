#
# Regular cron jobs for the yandex-anytask package
#
# ТЫ БУДЕШЬ ОСТАВЛЯТЬ ПУСТУЮ СТРОКУ В КОНЦЕ ЭТОГО ФАЙЛА
#

MAILTO=gebetix@yandex-team.ru
HOME=/opt/anytask

0   *   *   *   *  anytask     source /opt/anytask-env/bin/activate && cd /opt/anytask/anytask && python manage.py check_task_taken_expires --settings=settings_production
0   2   *   *   *  anytask     source /opt/anytask-env/bin/activate && cd /opt/anytask/anytask && python manage.py cleanup --settings=settings_production
0   3   *   *   *  anytask     source /opt/anytask-env/bin/activate && cd /opt/anytask/anytask && python manage.py check_invite_expires --settings=settings_production
0   4   *   *   *  anytask     source /opt/anytask-env/bin/activate && cd /opt/anytask/anytask && python manage.py cleanupregistration --settings=settings_production
*/5 *   *   *   *  anytask     source /opt/anytask-env/bin/activate && cd /opt/anytask/anytask && python manage.py check_contest