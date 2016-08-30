import json
from datetime import date, timedelta

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import generic
from moneyed import Money

from .forms import DishForm, IngredientForm, MealForm, TicketForm
from .models import (Dish, Ingredient, IngredientCategory, Meal, Product,
                     Ticket, Unit, UserProfile)


def get_profile(session):
    if not session.get('grain_active_user_profile'):
        # FIXME: ValidationError not quite appropriate
        raise ValidationError("No profile selected", code='invalid')
    return get_object_or_404(UserProfile,
                             pk=session['grain_active_user_profile'])

def cal_redirect(request):
    if not request.session.get('grain_active_user_profile'):
        return HttpResponseRedirect(reverse('grain:profile_list'))
    return HttpResponseRedirect(reverse('grain:calendar',
                                kwargs={'year': date.today().strftime("%Y"),
                                        'month': date.today().strftime("%m")}))


class ProfileList(generic.ListView):
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)


class ProfileCreate(generic.edit.CreateView):
    model = UserProfile
    fields = ['note', 'currency']
    success_url = reverse_lazy('grain:profile_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(ProfileCreate, self).form_valid(form)


def profile_select(request, pk):
    request.session['grain_active_user_profile'] \
        = get_object_or_404(UserProfile, pk=pk).pk
    return HttpResponseRedirect(reverse('grain:index'))


class MealMonthArchive(generic.dates.MonthArchiveView):
    date_field = "time"
    allow_empty, allow_future = True, True

    def get_queryset(self):
        return Meal.objects.filter(
            owner__pk=self.request.session['grain_active_user_profile'])

    def get_context_data(self, **kwargs):
        context = super(MealMonthArchive, self).get_context_data(**kwargs)
        month = date(int(self.kwargs['year']), int(self.kwargs['month']), 1)

        context['object_list'] = Meal.objects.filter(
            owner__pk=self.request.session['grain_active_user_profile'],
            time__gt=(month - timedelta(days=7)),
            time__lt=(month + timedelta(days=38)))
        context['meal_form'] = MealForm
        return context


class MealDetail(generic.DetailView):
    model = Meal

    def get_queryset(self):
        return Meal.objects.filter(
            owner__pk=self.request.session['grain_active_user_profile'])

    def get_context_data(self, **kwargs):
        context = super(MealDetail, self).get_context_data(**kwargs)
        context['cost_total'] = self.object.cost_closed + self.object.cost_open
        if context['cost_total']:
            context['cost_pc_closed'] = 100 * self.object.cost_closed \
                                            / context['cost_total']
            context['cost_pc_open'] = 100 * self.object.cost_open \
                                          / context['cost_total']
        context['dish_form'] = DishForm(initial={'meal': self.object})
        context['choices'] = Dish.COOKING_STYLES
        return context


class MealCreate(generic.edit.CreateView):
    model = Meal
    form_class = MealForm

    def form_valid(self, form):
        profile = get_profile(self.request.session)

        form.instance.owner = profile
        form.instance.cost_closed = Money(0, profile.currency)
        form.instance.cost_open = Money(0, profile.currency)
        return super(MealCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('grain:meal_detail', args=[self.object.id])


class MealDelete(generic.edit.DeleteView):
    model = Meal

    def get_queryset(self):
        return Meal.objects.filter(
            owner__pk=self.request.session['grain_active_user_profile'])

    def get_success_url(self):
        return reverse('grain:calendar', kwargs={
            'year': self.object.time.strftime("%Y"),
            'month': self.object.time.strftime("%m")})


class DishCreate(generic.edit.CreateView):
    model = Dish
    form_class = DishForm

    def form_valid(self, form):
        profile = get_profile(self.request.session)

        if form.instance.meal.owner != profile:
            raise ValidationError("Wrong profile", code='invalid')
        form.instance.cost_closed = Money(0, profile.currency)
        form.instance.cost_open = Money(0, profile.currency)
        for datum in form.data:
            if '_choice_' in datum:
                form.instance.method = datum[8:]
                break
        if form.instance.method not in [k for k, v in Dish.COOKING_STYLES]:
            raise ValidationError("Invalid cooking style", code='invalid')
        return super(DishCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('grain:meal_detail', args=[self.object.meal.id])


class DishDelete(generic.edit.DeleteView):
    model = Dish

    def get_queryset(self):
        profile = get_profile(self.request.session)
        return Dish.objects.filter(
            meal__owner__pk=self.request.session['grain_active_user_profile'])

    def get_success_url(self):
        return reverse('grain:meal_detail', args=[self.object.meal.id])


class IngredientListFull(generic.ListView):
    def get_queryset(self):
        # TODO: redirect if no profile
        return Ingredient.objects.filter(
            owner__pk=self.request.session['grain_active_user_profile'])

    def get_context_data(self, **kwargs):
        profile = get_profile(self.request.session)

        context = super(IngredientListFull, self).get_context_data(**kwargs)
        context['full'] = self.__class__ == IngredientListFull
        context['ingredient_form'] = \
            IngredientForm(initial={'price': Money(0, profile.currency)})
        return context


class IngredientList(IngredientListFull):
    def get_queryset(self):
        return super(IngredientList, self).get_queryset()\
                                          .filter(exhausted=False)

    def get_context_data(self, **kwargs):
        context = super(IngredientList, self).get_context_data(**kwargs)
        context['full'] = False
        return context


class IngredientDetail(generic.DetailView):
    model = Ingredient

    def get_queryset(self):
        return Ingredient.objects.filter(
            owner__pk=self.request.session['grain_active_user_profile'])

    def post(self, *args, **kwargs):
        profile = get_profile(self.request.session)
        ingredient = get_object_or_404(Ingredient, pk=kwargs.get('pk'),
                                       owner=profile)

        if 'finalise' in self.request.POST:
            ingredient.set_exhausted(True)
        elif 'definalise' in self.request.POST:
            ingredient.set_exhausted(False)
        return HttpResponseRedirect(reverse('grain:ingredient_detail',
                                            args=[ingredient.pk]))


class IngredientCreate(generic.edit.CreateView):
    model = Ingredient
    form_class = IngredientForm
    success_url = reverse_lazy('grain:inventory')
    template_name = "grain/generic_form.html"

    def form_valid(self, form):
        profile = get_profile(self.request.session)

        if form.instance.price.currency.code != profile.currency:
            raise ValidationError("Must use same currency as profile")
        form.instance.owner = profile
        if form.instance.product.fixed:
            form.instance.amount = form.instance.product.amount
        return super(IngredientCreate, self).form_valid(form)


class UnitList(generic.ListView):
    model = Unit


class UnitCreate(PermissionRequiredMixin, generic.edit.CreateView):
    permission_required = 'grain.can_create_unit'
    model = Unit
    fields = ['verbose', 'plural', 'short']
    success_url = reverse_lazy('grain:unit_list')


class CategoryList(generic.ListView):
    queryset = IngredientCategory.objects.filter(parent=None)
    template_name = "grain/category_list.html"


class CategoryCreate(PermissionRequiredMixin, generic.edit.CreateView):
    permission_required = 'grain.can_create_ingredient_category'
    model = IngredientCategory
    fields = ['parent', 'name']
    template_name = "grain/category_form.html"
    success_url = reverse_lazy('grain:category_list')


class ProductList(generic.ListView):
    def get_queryset(self):
        profile = get_profile(self.request.session)
        return Product.objects.filter(price__gt=Money(0, profile.currency))


def product_raw(request, pk):
    profile = get_profile(request.session)
    prod = get_object_or_404(Product, pk=pk,
                             price__gt=Money(0, profile.currency))
    prod_dict = {
        'name': prod.name,
        'usual_price': str(prod.price.amount),
        'amount': prod.amount,
        'units': prod.units.short,
        'fixed': prod.fixed,
    }
    return HttpResponse(json.dumps(prod_dict))


class ProductCreate(generic.edit.CreateView):
    model = Product
    fields = ['category', 'name', 'units', 'amount', 'fixed', 'price']
    success_url = reverse_lazy('grain:product_list')

    def form_valid(self, form):
        profile = get_profile(self.request.session)

        if form.instance.price.currency.code != profile.currency:
            raise ValidationError("Must use same currency as profile")
        return super(ProductCreate, self).form_valid(form)


def ticket_create(request):
    profile = get_profile(request.session)
    form = TicketForm(profile.pk, request.POST)
    if not form.is_valid():
        raise ValidationError("Invalid form", code='invalid')

    Ticket.objects.create_ticket(
        form.cleaned_data['ingredient'],
        form.cleaned_data['units_used'],
        form.cleaned_data['dish'],
        profile.currency,
        form.cleaned_data['exhausted'],
    )
    return HttpResponseRedirect(reverse("grain:meal_detail",
        args=[form.cleaned_data['dish'].meal.pk]))
