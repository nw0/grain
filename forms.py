import datetime

from django import forms
from django.utils.safestring import mark_safe

from .models import Meal


class BSDateInput(forms.TextInput):
    def render(self, name, value, attrs=None, choices=()):
        output = ['<div class="input-group date datepicker">',
                  super(BSDateInput, self).render(name, value, attrs),
                  '<span class="input-group-addon">',
                  '<i class="glyphicon glyphicon-calendar"></i></span>']
        return mark_safe('\n'.join(output))


class MealForm(forms.ModelForm):
    time = forms.DateField(label="Date", initial=datetime.date.today,
                           widget=BSDateInput())

    class Meta:
        model = Meal
        fields = ['time', 'meal_type', 'consumer']
