# encoding: utf-8

from datetime import datetime

from django.db import models

from django.contrib.auth.models import User

from tasks.models import Task

class EasyCiTask(models.Model):
    student = models.ForeignKey(User, db_index=True, null=False, blank=False)
    task = models.ForeignKey(Task, db_index=True, null=False, blank=False)

    data = models.TextField(db_index=False, null=True, blank=True, verbose_name=u"Задача")

    checked = models.BooleanField(db_index=True, null=False, blank=False, default=False)
    teacher_comments = models.TextField(db_index=False, null=True, blank=True, verbose_name=u"Комментарий преподавателя")

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)

    def __unicode__(self):
        return unicode(u"{0}|{1}".format(self.student, self.task))

class EasyCiCheck(models.Model):
    CHECK_ACTION_PEP8 = u"style"
    CHECK_ACTION_TEST = u"tests"
    CHECK_ACTION_HIDDEN = u"hidden"

    TYPES_ORDER = [CHECK_ACTION_PEP8, CHECK_ACTION_TEST, CHECK_ACTION_HIDDEN]
    TYPES_HIDDEN = set((CHECK_ACTION_HIDDEN,))

    TYPES = (
        (CHECK_ACTION_PEP8, u'Style'),
        (CHECK_ACTION_TEST, u'Тесты'),
        (CHECK_ACTION_HIDDEN, u'Hidden'),
    )

    easy_ci_task = models.ForeignKey(EasyCiTask, db_index=True, null=False, blank=False)
    exit_status = models.IntegerField(db_index=False, null=True, blank=True)
    type = models.CharField(max_length=32, choices=TYPES, db_index=False, null=True, blank=True)

    output = models.TextField(db_index=False, null=True, blank=True)

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)

    def type_name(self):
        for type_id, type_name in self.TYPES:
            if type_id == self.type:
                return type_name

        return self.type