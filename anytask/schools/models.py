from django.db import models
from django.core.urlresolvers import reverse
from courses.models import Course


# Create your models here.

class School(models.Model):
    name = models.CharField(max_length=191, db_index=True, null=False, blank=False)
    link = models.CharField(max_length=191, db_index=False, null=False, blank=False)
    courses = models.ManyToManyField(Course, blank=True)

    def __unicode__(self):
        return unicode(self.name)

    def get_full_name(self):
        return unicode(self.name)

    def get_absolute_url(self):
        return reverse('schools.views.school_page', args=[str(self.link)])
