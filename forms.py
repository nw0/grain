import datetime

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from moneyed import Money

from .models import Consumer, Dish, Ingredient, Meal, Product, UserProfile


class BSDateInput(forms.TextInput):
    def render(self, name, value, attrs=None, choices=()):
        output = ['<div class="input-group date datepicker">',
                  super(BSDateInput, self).render(name, value, attrs),
                  '<span class="input-group-addon">',
                  '<i class="glyphicon glyphicon-calendar"></i></span></div>']
        return mark_safe('\n'.join(output))


class UsernameForm(forms.Form):
    user = forms.ModelChoiceField(widget=forms.TextInput(),
                                  queryset=User.objects.all(),
                                  to_field_name='username')


class ConsumerForm(forms.ModelForm):
    owner = forms.ModelChoiceField(widget=forms.HiddenInput(),
                                   queryset=UserProfile.objects.all())
    actual_user = forms.ModelChoiceField(widget=forms.HiddenInput(),
                                         queryset=User.objects.all(),
                                         required=False)
    username = forms.CharField(max_length=30, required=False,
                               help_text="Specifying a user is optional")

    def __init__(self, profile, *args, **kwargs):
        super(ConsumerForm, self).__init__(*args, **kwargs)
        self.fields['owner'].initial = profile

    def clean(self):
        cleaned_data = super(ConsumerForm, self).clean()
        cleaned_data['owner'] = self.fields['owner'].initial

        if Consumer.objects.filter(owner=cleaned_data['owner'],
                                   name=cleaned_data['name']):
            self.add_error('name', "Already have a consumer with that name")
        if cleaned_data['username']:
            try:
                user = User.objects.get(username=self.cleaned_data['username'])
            except:
                user = None
                self.add_error('username', "Couldn't find user")
            cleaned_data['actual_user'] = user

        if cleaned_data['actual_user'] and cleaned_data['owner'].consumer_set.\
                filter(actual_user=cleaned_data['actual_user']).exists():
            self.add_error('username',
                           "This user is already a consumer in your profile")

    class Meta:
        model = Consumer
        fields = ['name', 'actual_user', 'owner']


class MealForm(forms.ModelForm):
    time = forms.DateField(label="Date", initial=datetime.date.today,
                           widget=BSDateInput())

    def __init__(self, profile_id=None, *args, **kwargs):
        super(MealForm, self).__init__(*args, **kwargs)
        if profile_id is not None:
            self.fields['consumer'].queryset = Consumer.objects.filter(
                owner__pk=profile_id)
        else:
            raise PermissionDenied

    class Meta:
        model = Meal
        fields = ['time', 'meal_type', 'consumer']


class DishForm(forms.ModelForm):
    meal = forms.ModelChoiceField(widget=forms.HiddenInput(),
                                  queryset=Meal.objects.all())

    class Meta:
        model = Dish
        fields = ['meal']


def product_listing(currency):
    products = {}
    for p in Product.objects.filter(price__gt=Money(0, currency)):
        v = str(p.vendor) if p.vendor else "Other"
        if v not in products:
            products[v] = []
        products[v].append((p.pk, p))
    return products.items()


class ProductForm(forms.ModelForm):
    def __init__(self, currency=None, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        if currency:
            self.fields['price'].initial = Money(0, currency)

    def clean(self):
        cleaned_data = super(ProductForm, self).clean()
        init_currency = self.fields['price'].initial.currency
        if init_currency and cleaned_data['price'].currency != init_currency:
            self.add_error('price', "Must use same currency as profile")
        elif cleaned_data['price'].amount < 0:
            self.add_error('price', "Must be positive")
        if cleaned_data['amount'] < 0:
            self.add_error('amount', "Must be positive")

    class Meta:
        model = Product
        fields = ['category', 'vendor', 'name', 'units', 'amount', 'fixed',
                  'price']


class IngredientForm(forms.ModelForm):
    amount = forms.FloatField(required=False)
    expiry_type = forms.ChoiceField(widget=forms.RadioSelect(),
                                    choices=Ingredient.EXP_CHOICES,
                                    initial=Ingredient.BEST_BEFORE)
    best_before = forms.DateField(label="Best before", widget=BSDateInput())
    purchase_date = forms.DateField(label="Purchased on", widget=BSDateInput(),
                                    initial=datetime.date.today)
    partial = forms.BooleanField(required=False,
        help_text="e.g. if adding half a bottle of spices")

    def __init__(self, currency="GBP", *args, **kwargs):
        super(IngredientForm, self).__init__(*args, **kwargs)
        self.fields['product'].choices = product_listing(currency)
        self.fields['price'].initial = Money(0, currency)

    def clean(self):
        cleaned_data = super(IngredientForm, self).clean()
        if cleaned_data['price'].currency != \
                self.fields['price'].initial.currency:
            self.add_error('price', "Must use same currency as profile")
        elif cleaned_data['price'].amount < 0:
            self.add_error('price', "Must be positive")
        if cleaned_data['product'].fixed and not cleaned_data['partial']:
            self.cleaned_data['amount'] = cleaned_data['product'].amount
        if cleaned_data['amount'] < 0:
            self.add_error('amount', "Must be positive")

    class Meta:
        model = Ingredient
        fields = ['product', 'price', 'amount', 'best_before', 'expiry_type',
                  'purchase_date']


class TicketForm(forms.Form):
    dish = forms.ModelChoiceField(widget=forms.HiddenInput(),
                                  queryset=Dish.objects.all())
    ingredient = forms.ModelChoiceField(
        queryset=Ingredient.objects.filter(exhausted=False))
    units_used = forms.FloatField()
    exhausted = forms.BooleanField(required=False)

    def __init__(self, profile_pk=None, *args, **kwargs):
        super(TicketForm, self).__init__(*args, **kwargs)
        self.fields['ingredient'].queryset = Ingredient.objects.filter(
            exhausted=False, owner__pk=profile_pk
        ).order_by('product__category__name', '-used_amount')
        self.fields['dish'].queryset = Dish.objects.filter(
            meal__owner__pk=profile_pk)
