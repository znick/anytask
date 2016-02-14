from django.core.exceptions import ValidationError
from django.forms import ModelForm, Textarea

from django_bootstrap.forms import BootstrapMixin

from easy_ci.models import EasyCiTask
from tasks.models import TaskTaken

class RunForm(ModelForm, BootstrapMixin):
    class Meta:
        model = EasyCiTask
        fields = ['data']
        widgets = {
            'data' : Textarea(attrs={'style': 'height: 200px; width: 100%'}),
        }

class TaskTakenForm(ModelForm, BootstrapMixin):
    def __init__(self, score_max, *args, **kwargs):
        ModelForm.__init__(self, *args, **kwargs)
        BootstrapMixin.__init__(self)
        self.score_max = score_max

    def clean_score(self):
        if self.cleaned_data["score"] > self.score_max:
            raise ValidationError(u"Maximum scrore is: {0}".format(self.score_max), code='invalid', params={'score_max' : self.score_max})

        return self.cleaned_data["score"]

    class Meta:
        model = TaskTaken
        fields = ['score', 'teacher_comments']
        widgets = {
            'teacher_comments' : Textarea(attrs={'style': 'height: 200px; width: 100%'}),
        }
