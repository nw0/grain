from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import generic
from moneyed import Money

from .forms import DishForm, IngredientForm, MealForm
from .models import (Dish, Ingredient, IngredientCategory, Meal, Product, Unit,
                     UserProfile)


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
        return context


class MealCreate(generic.edit.CreateView):
    model = Meal
    form_class = MealForm

    def form_valid(self, form):
        if not self.request.session.get('grain_active_user_profile'):
            # FIXME: ValidationError not quite appropriate
            raise ValidationError("No profile selected", code='invalid')
        profile = get_object_or_404(UserProfile,
            pk=self.request.session['grain_active_user_profile'])

        form.instance.owner = profile
        form.instance.cost_closed = Money(0, profile.currency)
        form.instance.cost_open = Money(0, profile.currency)
        return super(MealCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('grain:meal_detail', args=[self.object.id])


class DishCreate(generic.edit.CreateView):
    model = Dish
    form_class = DishForm

    def form_valid(self, form):
        if not self.request.session.get('grain_active_user_profile'):
            # FIXME: ValidationError not quite appropriate
            raise ValidationError("No profile selected", code='invalid')
        profile = get_object_or_404(UserProfile,
            pk=self.request.session['grain_active_user_profile'])

        if form.instance.meal.owner != profile:
            raise ValidationError("Wrong profile", code='invalid')
        form.instance.cost_closed = Money(0, profile.currency)
        form.instance.cost_open = Money(0, profile.currency)
        return super(DishCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('grain:meal_detail', args=[self.object.meal.id])


class IngredientList(generic.ListView):
    def get_queryset(self):
        # TODO: redirect if no profile
        return Ingredient.objects.filter(exhausted=False,
            owner__pk=self.request.session['grain_active_user_profile'])

    def get_context_data(self, **kwargs):
        if not self.request.session.get('grain_active_user_profile'):
            # FIXME: ValidationError not quite appropriate
            raise ValidationError("No profile selected", code='invalid')
        profile = get_object_or_404(UserProfile,
            pk=self.request.session['grain_active_user_profile'])

        context = super(IngredientList, self).get_context_data(**kwargs)
        context['ingredient_form'] = \
            IngredientForm(initial={'price': Money(0, profile.currency)})
        return context


class IngredientListFull(generic.ListView):
    # TODO: consider subclassing with InventoryList
    def get_queryset(self):
        # TODO: redirect if no profile
        return Ingredient.objects.filter(
            owner__pk=self.request.session['grain_active_user_profile'])

    def get_context_data(self, **kwargs):
        if not self.request.session.get('grain_active_user_profile'):
            # FIXME: ValidationError not quite appropriate
            raise ValidationError("No profile selected", code='invalid')
        profile = get_object_or_404(UserProfile,
            pk=self.request.session['grain_active_user_profile'])

        context = super(IngredientListFull, self).get_context_data(**kwargs)
        context['full'] = True
        context['ingredient_form'] = \
            IngredientForm(initial={'price': Money(0, profile.currency)})
        return context


class UnitList(generic.ListView):
    model = Unit


class UnitCreate(generic.edit.CreateView):
    model = Unit
    fields = ['verbose', 'plural', 'short']
    success_url = reverse_lazy('grain:unit_list')


class CategoryList(generic.ListView):
    queryset = IngredientCategory.objects.filter(parent=None)
    template_name = "grain/category_list.html"


class CategoryCreate(generic.edit.CreateView):
    model = IngredientCategory
    fields = ['parent', 'name']
    template_name = "grain/category_form.html"
    success_url = reverse_lazy('grain:category_list')


class ProductList(generic.ListView):
    def get_queryset(self):
        if not self.request.session.get('grain_active_user_profile'):
            # FIXME: ValidationError not quite appropriate
            raise ValidationError("No profile selected", code='invalid')
        profile = get_object_or_404(UserProfile,
            pk=self.request.session['grain_active_user_profile'])

        return Product.objects.filter(price__gt=Money(0, profile.currency))


class ProductCreate(generic.edit.CreateView):
    model = Product
    fields = ['category', 'name', 'units', 'amount', 'fixed', 'price']
    success_url = reverse_lazy('grain:product_list')

    # FIXME: only allow adding in profile currency
