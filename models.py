from datetime import date

from django.contrib.auth.models import User
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from djmoney.models.fields import CurrencyField, MoneyField
from moneyed import Money


class UserProfile(models.Model):
    """Profile for Grain

    A profile will handle ingredients and meals in a single currency.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.CharField(max_length=24)
    currency = CurrencyField(default='GBP')

    @python_2_unicode_compatible
    def __str__(self):
        return "%s %s: %s" % (self.user, self.currency, self.note)


class Consumer(models.Model):
    owner = models.ForeignKey(UserProfile)
    actual_user = models.ForeignKey(User, blank=True, null=True)
    name = models.CharField(max_length=20)

    @python_2_unicode_compatible
    def __str__(self):
        return self.name


class Unit(models.Model):
    """Custom unit class for groceries"""
    short = models.CharField("abbreviation", max_length=8)
    verbose = models.CharField("name (singular)", max_length=20)
    plural = models.CharField(max_length=20)

    @python_2_unicode_compatible
    def __str__(self):
        return self.short


class IngredientCategory(models.Model):
    """Cascading categories for ingredients"""
    parent = models.ForeignKey('self', default=None, blank=True, null=True)
    name = models.CharField(max_length=40)

    def get_parent_name_list(self):
        li = self.parent.get_parent_name_list() if self.parent else []
        li.append(self.name)
        return li

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

    def update_usage(self, delta):
        assert not self.exhausted, "Ingredient has been exhausted"

        self.used_amount += delta
        affected_tickets = self.ticket_set.all()
        for ticket in affected_tickets:
            ticket.update_cost(self.price / self.used_amount)
        self.save()
        return self.price / self.used_amount

    def set_exhausted(self, exhausted):
        if exhausted != self.exhausted:
            for ticket in self.ticket_set.all():
                ticket.set_final(exhausted)
            self.exhausted = exhausted
            self.save()

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
    consumer = models.ForeignKey(Consumer, blank=True, null=True)

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

    def costs_open_change(self, delta):
        self.cost_open += delta
        self.save()

        self.meal.cost_open += delta
        self.meal.save()

    def costs_close(self, delta):
        self.cost_closed += delta
        self.cost_open -= delta
        self.save()

        self.meal.cost_closed += delta
        self.meal.cost_open -= delta
        self.meal.save()

    def get_ticket_form(self, profile_pk=None):
        from .forms import TicketForm
        return TicketForm(profile_pk, initial={'dish': self})

    class Meta:
        verbose_name_plural = "dishes"

    @python_2_unicode_compatible
    def __str__(self):
        tickets = self.ticket_set.all().order_by('-cost')
        if tickets.distinct().count() == 0:
            return "%s (empty)" % self.method
        return "%s %s" % (self.get_method_display(), tickets[0])


class TicketManager(models.Manager):
    def create_ticket(self, ingredient, used_on_ticket, dish, currency,
                      exhausted=False):
        assert used_on_ticket > 0, "Must use positive quantity"
        assert not ingredient.exhausted, "Ingredient must not be exhausted"

        ticket = self.create(ingredient=ingredient, used=used_on_ticket,
                             dish=dish, cost=Money(0, currency))
        ticket.save()
        ingredient.update_usage(used_on_ticket)
        if exhausted:
            ingredient.set_exhausted(True)
        return ticket


class Ticket(models.Model):
    # FIXME: include docstring
    objects = TicketManager()

    ingredient = models.ForeignKey(Ingredient)
    used = models.FloatField()
    cost = MoneyField(max_digits=10, decimal_places=4)
    final = models.BooleanField(default=False)
    dish = models.ForeignKey(Dish)

    def update_cost(self, cost_per_unit):
        assert not self.final, "Cannot modify finalised tickets"
        new_cost = self.used * cost_per_unit
        self.dish.costs_open_change(new_cost - self.cost)
        self.cost = new_cost
        self.save()

    def set_final(self, final):
        if final != self.final:
            if final:
                self.dish.costs_close(self.cost)
            else:
                self.dish.costs_close(-self.cost)
            self.final = final
            self.save()

    @python_2_unicode_compatible
    def __str__(self):
        return "%s [%s]" % (self.ingredient, self.used)


# TODO: event log
