from datetime import date

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

    class Meta:
        verbose_name_plural = "ingredient categories"

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
    fixed = models.BooleanField(default=True)

    @python_2_unicode_compatible
    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Specific instances of ingredients"""
    BEST_BEFORE, EXPIRES = "BBF", "EXP"
    EXP_CHOICES = (
        (BEST_BEFORE, "best before"),
        (EXPIRES, "expires")
    )

    owner = models.ForeignKey(UserProfile)
    product = models.ForeignKey(Product)
    price = MoneyField(max_digits=10, decimal_places=2, default_currency='GBP')
    amount = models.FloatField()
    used_amount = models.FloatField(default=0)
    best_before = models.DateField(blank=True)
    expiry_type = models.CharField(max_length=3, choices=EXP_CHOICES)
    purchase_date = models.DateField(default=date.today)
    exhausted = models.BooleanField(default=False)

    @python_2_unicode_compatible
    def __str__(self):
        return "%s" % self.product


class Meal(models.Model):
    # FIXME: include docstring
    BREAKFAST, LUNCH, DINNER, SUPPER, TEA, SNACK = 0, 1, 2, 3, 4, 5
    MEAL_CHOICES = (
        (BREAKFAST, "Breakfast"),
        (LUNCH,     "Lunch"),
        (DINNER,    "Dinner"),
        (SUPPER,    "Supper"),
        (TEA,       "Tea"),
        (SNACK,     "Snack"),
    )
    owner = models.ForeignKey(UserProfile)
    time = models.DateTimeField()
    meal_type = models.IntegerField(choices=MEAL_CHOICES)
    cost_closed = MoneyField(max_digits=10, decimal_places=4)
    cost_open = MoneyField(max_digits=10, decimal_places=4)

    @python_2_unicode_compatible
    def __str__(self):
        return "%s on %s" % (self.get_meal_type_display(), self.time)


class Dish(models.Model):
    # FIXME: include docstring
    COOKING_STYLES = (
        ('frying',      "Fried"),
        ('boiling',     "Boiled"),
        ('baking',      "Baked"),
        ('roasting',    "Roasted"),
        ('uncooked',    "Uncooked"),
        ('instant',     "Microwaved")
    )
    method = models.CharField(max_length=8, choices=COOKING_STYLES)
    meal = models.ForeignKey(Meal)
    cost_closed = MoneyField(max_digits=10, decimal_places=4)
    cost_open = MoneyField(max_digits=10, decimal_places=4)

    class Meta:
        verbose_name_plural = "dishes"

    @python_2_unicode_compatible
    def __str__(self):
        tickets = self.ticket_set.all().order_by('-cost')
        if tickets.distinct().count() == 0:
            return "%s (empty)" % self.method
        return "%s %s" % (self.get_method_display(), tickets[0])


class Ticket(models.Model):
    # FIXME: include docstring
    ingredient = models.ForeignKey(Ingredient)
    used = models.FloatField()
    cost = MoneyField(max_digits=10, decimal_places=4)
    final = models.BooleanField(default=False)
    dish = models.ForeignKey(Dish)

    @python_2_unicode_compatible
    def __str__(self):
        return "%s [%s]" % (self.ingredient, self.used)


# TODO: event log
