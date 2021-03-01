from django.db import models
from django.contrib.auth.models import User

from years.models import Year


class Group(models.Model):
    year = models.ForeignKey(Year, db_index=True, null=False, blank=True)
    name = models.CharField(max_length=191, db_index=True, null=False, blank=True)
    students = models.ManyToManyField(User, blank=True)

    added_time = models.DateTimeField(auto_now_add=True)  # remove default=timezone.now
    update_time = models.DateTimeField(auto_now=True)  # remove default=timezone.now

    class Meta:
        unique_together = (("year", "name"),)

    def __unicode__(self):
        return u"{0}|{1}".format(self.year, unicode(self.name))

    def get_full_name(self):
        return unicode(self.name)
