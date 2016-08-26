import datetime

from django import forms
from django.utils.safestring import mark_safe

from .models import Dish, Ingredient, Meal


class BSDateInput(forms.TextInput):
    def render(self, name, value, attrs=None, choices=()):
        output = ['<div class="input-group date datepicker">',
                  super(BSDateInput, self).render(name, value, attrs),
                  '<span class="input-group-addon">',
                  '<i class="glyphicon glyphicon-calendar"></i></span></div>']
        return mark_safe('\n'.join(output))


class MealForm(forms.ModelForm):
    time = forms.DateField(label="Date", initial=datetime.date.today,
                           widget=BSDateInput())

    class Meta:
        model = Meal
        fields = ['time', 'meal_type', 'consumer']


class DishForm(forms.ModelForm):
    meal = forms.ModelChoiceField(widget=forms.HiddenInput(),
                                  queryset=Meal.objects.all())

    class Meta:
        model = Dish
        fields = ['method', 'meal']


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['product', 'price', 'amount', 'best_before', 'expiry_type',
                  'purchase_date']
