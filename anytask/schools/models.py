from django.db import models
from courses.models import Course

# Create your models here.

class School(models.Model):

    name = models.CharField(max_length=254, db_index=True, null=False, blank=False)
    link = models.CharField(max_length=254, db_index=False, null=False, blank=False)
    courses = models.ManyToManyField(Course, null=True, blank=True)
