from django.db import models
from datetime import datetime

class Year(models.Model):
    start_year = models.IntegerField(db_index=True, null=False, blank=False, unique=True)

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)
    
    def __unicode__(self):
        return u"{0}-{1}".format(self.start_year, self.start_year + 1)