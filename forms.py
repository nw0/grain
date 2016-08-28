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
        fields = ['meal']


class IngredientForm(forms.ModelForm):
    amount = forms.FloatField(required=False)
    expiry_type = forms.ChoiceField(widget=forms.RadioSelect(),
                                    choices=Ingredient.EXP_CHOICES,
                                    initial=Ingredient.BEST_BEFORE)
    best_before = forms.DateField(label="Best before", widget=BSDateInput())
    purchase_date = forms.DateField(label="Purchased on", widget=BSDateInput(),
                                    initial=datetime.date.today)

    class Meta:
        model = Ingredient
        fields = ['product', 'price', 'amount', 'best_before', 'expiry_type',
                  'purchase_date']


class TicketForm(forms.Form):
    dish = forms.ModelChoiceField(widget=forms.HiddenInput(),
                                  queryset=Dish.objects.all())
    ingredient = forms.ModelChoiceField(queryset=Ingredient.objects.all())
    units_used = forms.FloatField()
    exhausted = forms.BooleanField(required=False)
