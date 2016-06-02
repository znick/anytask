from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from datetime import datetime

from years.common import get_current_year
from groups.models import Group

class UserProfile(models.Model):
    user = models.ForeignKey(User, db_index=True, null=False, blank=False, unique=True)
    second_name = models.CharField(max_length=128, db_index=True, null=True, blank=True)

    avatar = models.ImageField('profile picture', upload_to='static/media/images/avatars/', blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    unit = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    position = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    academic_degree = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    academic_title = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)


    ya_uid = models.IntegerField(null=True, blank=True)
    ya_login = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    ya_contest_oauth = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    ya_passport_oauth = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)



    def is_current_year_student(self):
        return Group.objects.filter(year=get_current_year()).filter(students=self.user).count() > 0

    def __unicode__(self):
            return unicode(self.user)

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)
