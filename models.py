from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from djmoney.models.fields import CurrencyField, MoneyField
from moneyed import Money


@python_2_unicode_compatible
class GrainEvent(models.Model):
    CREATE, EDIT, DELETE = "creation", "update", "deletion"
    LOG_ACTIONS = (
        (CREATE, "Create"),
        (EDIT, "Edit"),
        (DELETE, "Delete")
    )

    action = models.CharField(choices=LOG_ACTIONS, max_length=20)
    model = models.CharField(max_length=30)
    object_pk = models.IntegerField()
    user = models.ForeignKey(User)
    time = models.DateField(auto_now_add=True)

    def __str__(self):
        return "%s %s (%s)" % (self.model, self.action, self.user)


@python_2_unicode_compatible
class UserProfile(models.Model):
    """Profile for Grain

    A profile will handle ingredients and meals in a single currency.
    """
    user = models.ManyToManyField(User)
    note = models.CharField(max_length=24)
    currency = CurrencyField(default='GBP')

    def add_user(self, user):
        self.user.add(user)

    def __str__(self):
        return "%s: %s" % (self.currency, self.note)


@python_2_unicode_compatible
class Consumer(models.Model):
    owner = models.ForeignKey(UserProfile)
    actual_user = models.ForeignKey(User, blank=True, null=True)
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Unit(models.Model):
    """Custom unit class for groceries"""
    short = models.CharField("abbreviation", max_length=8)
    verbose = models.CharField("name (singular)", max_length=20)
    plural = models.CharField(max_length=20)

    def __str__(self):
        return self.short


@python_2_unicode_compatible
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

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Vendor(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Product(models.Model):
    """Classes of ingredients, in specific units and packaging"""
    name = models.CharField(max_length=60)
    vendor = models.ForeignKey(Vendor, blank=True, null=True, default=None)
    category = models.ForeignKey(IngredientCategory)
    price = MoneyField(max_digits=10, decimal_places=2, default_currency='GBP')
    amount = models.FloatField()
    units = models.ForeignKey(Unit)
    fixed = models.BooleanField(default=True)

    def __str__(self):
        return "%s %s" % (self.vendor if self.vendor else "Other", self.name)


@python_2_unicode_compatible
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
        if self.used_amount != 0:
            cpu = self.price * (1 / self.used_amount)
        else:
            cpu = Money(0, self.price.currency.code)
        for ticket in self.ticket_set.all():
            ticket.update_cost(cpu)
        self.save()
        return cpu

    def set_exhausted(self, exhausted):
        if exhausted != self.exhausted:
            for ticket in self.ticket_set.all():
                ticket.set_final(exhausted)
            self.exhausted = exhausted
            self.save()

    def __str__(self):
        return "%s" % self.product


@python_2_unicode_compatible
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
    consumer = models.ForeignKey(Consumer)

    def cost_progress_breakdown(self):
        cost_tot, pc_closed, pc_open = self.cost_closed + self.cost_open, 0, 0
        if cost_tot:
            pc_closed = 100 * self.cost_closed.amount / cost_tot.amount
            pc_open = 100 * self.cost_open.amount / cost_tot.amount
        return (cost_tot, pc_closed, pc_open)

    def __str__(self):
        return "%s on %s" % (self.get_meal_type_display(), self.time.strftime("%F"))


@python_2_unicode_compatible
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

        ticket = self.create(ingredient=ingredient, used=0,
                             dish=dish, cost=Money(0, currency))
        ticket.update_usage(used_on_ticket)
        if exhausted:
            ingredient.set_exhausted(True)
        return ticket


@python_2_unicode_compatible
class Ticket(models.Model):
    # FIXME: include docstring
    objects = TicketManager()

    ingredient = models.ForeignKey(Ingredient)
    used = models.FloatField()
    cost = MoneyField(max_digits=10, decimal_places=4)
    final = models.BooleanField(default=False)
    dish = models.ForeignKey(Dish)

    def update_usage(self, delta):
        self.used += delta
        self.save()
        self.ingredient.update_usage(delta)

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

    def __str__(self):
        return "%s [%s]" % (self.ingredient, self.used)


@receiver(signals.pre_delete, sender=Ticket)
def clean_ticket(sender, **kwargs):
    ticket = kwargs.get('instance')
    was_final = ticket.final

    if was_final:
        ticket.ingredient.set_exhausted(False)
        ticket.final = False

    ticket.update_usage(-ticket.used)

    if was_final:
        ticket.ingredient.set_exhausted(True)
