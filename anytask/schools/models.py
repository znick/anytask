from django.db import models
from schools.models import School

# Create your models here.

class School(models.Model):

    name = models.CharField(max_length=254, db_index=True, null=False, blank=False)
    courses = models.ManyToManyField(Course, null=True, blank=True)
