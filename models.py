from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from djmoney.models.fields import CurrencyField, MoneyField


class UserProfile(models.Model):
    """Profile for Grain

    A profile will handle ingredients and meals in a single currency.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    note = models.CharField(max_length=24)
    currency = CurrencyField(default='GBP')

    @python_2_unicode_compatible
    def __str__(self):
        return "%s %s: %s" % (self.user, self.currency, self.note)


class Unit(models.Model):
    """Custom unit class for groceries"""
    short = models.CharField(max_length=8)
    verbose = models.CharField(max_length=20)
    plural = models.CharField(max_length=20)

    @python_2_unicode_compatible
    def __str__(self):
        return self.short


class IngredientCategory(models.Model):
    """Cascading categories for ingredients"""
    parent = models.ForeignKey('self', default=None, blank=True, null=True)
    name = models.CharField(max_length=40)

    # FIXME: is verbose_name required?

    @python_2_unicode_compatible
    def __str__(self):
        return self.name


class Product(models.Model):
    """Classes of ingredients, in specific units and packaging"""
    name = models.CharField(max_length=60)
    category = models.ForeignKey(IngredientCategory)
    price = MoneyField(max_digits=10, decimal_places=2, default_currency='GBP')
    amount = models.FloatField()
    units = models.ForeignKey(Unit)

    @python_2_unicode_compatible
    def __str__(self):
        return self.name


# TODO: class Ingredient
# TODO: class Ticket
# TODO: class Dish
# TODO: class Meal
