#coding: utf-8

from django import forms
import os

class PdfForm(forms.Form):
    pdf = forms.FileField(required=False)
    def __init__(self, *args, **kwargs):
        self.extensions = kwargs.pop('extensions', None)
        super(PdfForm, self).__init__(*args, **kwargs)
    def clean_pdf(self):
        file = self.cleaned_data.get('pdf')
        if file:
            name, extension = os.path.splitext(file.name)
            if extension not in self.extensions:
                raise forms.ValidationError(u'Файл должен иметь одно из расширений: ' + ",".join(self.extensions))


class QueueForm(forms.Form):
    rework = forms.BooleanField(initial=False, label='На доработке', required=False)
    verefication = forms.BooleanField(initial=True, label='На провеерке', required=False)
    mine = forms.BooleanField(initial=True, label='Мои задачи', required=False)
    following = forms.BooleanField(initial=True, label='Наблюдаемые мной', required=False)
    not_mine = forms.BooleanField(initial=True, label='Не мои', required=False)
    not_owned = forms.BooleanField(initial=True, label='Ничьи', required=False)
    overdue = forms.IntegerField(initial=0, label='Ждут проверки несколько дней')
