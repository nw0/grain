from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from djmoney.models.fields import CurrencyField


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


class IngredientCategory(models.Model):
    """Cascading categories for ingredients"""
    parent = models.ForeignKey('self', default=None, blank=True, null=True)
    name = models.CharField(max_length=40)

    # FIXME: is verbose_name required?

    @python_2_unicode_compatible
    def __str__(self):
        return self.name

# TODO: class IngredientType
# TODO: class Ingredient
# TODO: class Ticket
# TODO: class Dish
# TODO: class Meal
