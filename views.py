import json
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import (PermissionRequiredMixin,
                                        UserPassesTestMixin)
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import generic
from moneyed import Money

from .forms import DishForm, IngredientForm, MealForm, ProductForm, TicketForm
from .models import (Consumer, Dish, Ingredient, IngredientCategory, Meal,
                     Product, Ticket, Unit, UserProfile, Vendor)


def get_profile(session):
    if not session.get('grain_active_user_profile'):
        # FIXME: ValidationError not quite appropriate
        raise PermissionDenied("No profile selected")
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
        return self.request.user.userprofile_set.all()


class ProfileCreate(generic.edit.CreateView):
    model = UserProfile
    fields = ['note', 'currency']
    success_url = reverse_lazy('grain:profile_list')

    def form_valid(self, form):
        form.instance.save()
        form.instance.user.add(self.request.user)
        return super(ProfileCreate, self).form_valid(form)


class ProfileUpdate(UserPassesTestMixin, generic.edit.UpdateView):
    fields = ['user']
    template_name = 'grain/userprofile_update.html'
    success_url = reverse_lazy('grain:profile_list')
    login_url = reverse_lazy("grain:profile_list")

    def test_func(self):
        return 'grain_active_user_profile' in self.request.session

    def get_object(self):
        return get_object_or_404(UserProfile,
            pk=self.request.session['grain_active_user_profile'])


def profile_select(request, pk):
    # Try..except
    request.session['grain_active_user_profile'] \
        = request.user.userprofile_set.get(pk=pk).pk
    return HttpResponseRedirect(reverse('grain:index'))


class ConsumerList(UserPassesTestMixin, generic.ListView):
    login_url = reverse_lazy("grain:profile_list")

    def test_func(self):
        return 'grain_active_user_profile' in self.request.session

    def get_queryset(self):
        return Consumer.objects.filter(
            owner__pk=self.request.session['grain_active_user_profile'])


class ConsumerDetail(UserPassesTestMixin, generic.DetailView):
    login_url = reverse_lazy("grain:profile_list")

    def test_func(self):
        return 'grain_active_user_profile' in self.request.session

    def get_queryset(self):
        return Consumer.objects.filter(
            owner__pk=self.request.session['grain_active_user_profile'])


class ConsumerCreate(UserPassesTestMixin, generic.edit.CreateView):
    model = Consumer
    fields = ['name', 'actual_user']
    success_url = reverse_lazy('grain:consumer_list')
    login_url = reverse_lazy("grain:profile_list")

    def test_func(self):
        return 'grain_active_user_profile' in self.request.session

    def form_valid(self, form):
        form.instance.owner = get_profile(self.request.session)
        return super(ConsumerCreate, self).form_valid(form)


class MealMonthArchiveFull(UserPassesTestMixin, generic.dates.MonthArchiveView):
    date_field = "time"
    allow_empty, allow_future = True, True
    login_url = reverse_lazy("grain:profile_list")

    def test_func(self):
        return 'grain_active_user_profile' in self.request.session

    def get_queryset(self):
        month = date(int(self.kwargs['year']), int(self.kwargs['month']), 1)
        return Meal.objects.filter(
            owner__pk=self.request.session['grain_active_user_profile'],
            time__gt=(month - timedelta(days=7)),
            time__lt=(month + timedelta(days=38)))

    def get_context_data(self, **kwargs):
        context = super(MealMonthArchiveFull, self).get_context_data(**kwargs)
        month = date(int(self.kwargs['year']), int(self.kwargs['month']), 1)

        context['object_list'] = self.get_queryset()
        context['meal_form'] = MealForm(
            profile_id=self.request.session['grain_active_user_profile'])
        context['full'] = True
        context['link'] = "grain:calendar_all"
        context['profile'] = get_profile(self.request.session)
        return context

class MealMonthArchive(MealMonthArchiveFull):
    def get_queryset(self):
        month = date(int(self.kwargs['year']), int(self.kwargs['month']), 1)

        return Meal.objects.filter(consumer__actual_user=self.request.user,
            cost_open__gte=Money(0, get_profile(self.request.session).currency),
            time__gt=(month - timedelta(days=7)),
            time__lt=(month + timedelta(days=38)))

    def get_context_data(self, **kwargs):
        context = super(MealMonthArchive, self).get_context_data(**kwargs)
        context['full'] = False
        context['link'] = "grain:calendar"
        return context


class MealDayArchive(UserPassesTestMixin, generic.dates.DayArchiveView):
    date_field = "time"
    allow_empty, allow_future = True, True
    login_url = reverse_lazy("grain:profile_list")

    def test_func(self):
        return 'grain_active_user_profile' in self.request.session

    def get_queryset(self):
        return Meal.objects.filter(
            owner__pk=self.request.session['grain_active_user_profile'])


class MealDayArchiveSpecific(MealDayArchive):
    def get_queryset(self):
        return super(MealDayArchiveSpecific, self).get_queryset().filter(
            meal_type=self.kwargs['meal_type'])

    def get_context_data(self, **kwargs):
        context = super(MealDayArchiveSpecific, self).get_context_data(**kwargs)
        context['specific'] = True
        return context


class MealDetail(UserPassesTestMixin, generic.DetailView):
    login_url = reverse_lazy("grain:profile_list")

    def test_func(self):
        return 'grain_active_user_profile' in self.request.session

    def get_queryset(self):
        return Meal.objects.filter(
            owner__pk=self.request.session['grain_active_user_profile'])

    def get_context_data(self, **kwargs):
        context = super(MealDetail, self).get_context_data(**kwargs)
        context['costs'] = self.object.cost_progress_breakdown()
        context['dish_form'] = DishForm(initial={'meal': self.object})
        context['choices'] = Dish.COOKING_STYLES
        return context


class MealCreate(UserPassesTestMixin, generic.edit.CreateView):
    model = Meal
    form_class = MealForm
    login_url = reverse_lazy("grain:profile_list")

    def test_func(self):
        return 'grain_active_user_profile' in self.request.session

    def get_form_kwargs(self):
        kwargs = super(MealCreate, self).get_form_kwargs()
        kwargs['profile_id'] = self.request.session['grain_active_user_profile']
        return kwargs

    def form_valid(self, form):
        profile = get_profile(self.request.session)

        form.instance.owner = profile
        form.instance.cost_closed = Money(0, profile.currency)
        form.instance.cost_open = Money(0, profile.currency)
        return super(MealCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('grain:meal_detail', args=[self.object.id])


class MealDelete(UserPassesTestMixin, generic.edit.DeleteView):
    login_url = reverse_lazy("grain:profile_list")

    def test_func(self):
        return 'grain_active_user_profile' in self.request.session

    def get_queryset(self):
        return Meal.objects.filter(
            owner__pk=self.request.session['grain_active_user_profile'])

    def get_success_url(self):
        return reverse('grain:calendar', kwargs={
            'year': self.object.time.strftime("%Y"),
            'month': self.object.time.strftime("%m")})


class DishCreate(UserPassesTestMixin, generic.edit.CreateView):
    model = Dish
    form_class = DishForm
    login_url = reverse_lazy("grain:profile_list")

    def test_func(self):
        return 'grain_active_user_profile' in self.request.session

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


class DishDelete(UserPassesTestMixin, generic.edit.DeleteView):
    login_url = reverse_lazy("grain:profile_list")

    def test_func(self):
        return 'grain_active_user_profile' in self.request.session

    def get_queryset(self):
        return Dish.objects.filter(
            meal__owner__pk=self.request.session['grain_active_user_profile'])

    def get_success_url(self):
        return reverse('grain:meal_detail', args=[self.object.meal.id])


class IngredientListFull(UserPassesTestMixin, generic.ListView):
    login_url = reverse_lazy("grain:profile_list")

    def test_func(self):
        return 'grain_active_user_profile' in self.request.session

    def get_queryset(self):
        return Ingredient.objects.filter(
            owner=get_profile(self.request.session))

    def get_context_data(self, **kwargs):
        context = super(IngredientListFull, self).get_context_data(**kwargs)
        context['full'] = self.__class__ == IngredientListFull
        context['ingredient_form'] = \
            IngredientForm(currency=get_profile(self.request.session).currency)
        return context


class IngredientList(IngredientListFull):
    def get_queryset(self):
        return super(IngredientList, self).get_queryset()\
                                          .filter(exhausted=False)

    def get_context_data(self, **kwargs):
        context = super(IngredientList, self).get_context_data(**kwargs)
        context['full'] = False
        return context


class IngredientDetail(UserPassesTestMixin, generic.DetailView):
    login_url = reverse_lazy("grain:profile_list")

    def test_func(self):
        return 'grain_active_user_profile' in self.request.session

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


class IngredientCreate(UserPassesTestMixin, generic.edit.CreateView):
    model = Ingredient
    form_class = IngredientForm
    success_url = reverse_lazy('grain:inventory')
    template_name = "grain/generic_form.html"
    login_url = reverse_lazy("grain:profile_list")

    def test_func(self):
        return 'grain_active_user_profile' in self.request.session

    def get_form_kwargs(self):
        kwargs = super(IngredientCreate, self).get_form_kwargs()
        kwargs['currency'] = get_profile(self.request.session).currency
        return kwargs

    def form_valid(self, form):
        form.instance.owner = get_profile(self.request.session)
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

    def form_valid(self, form):
        if "_add_another" in self.request.POST:
            self.success_url = reverse('grain:category_create')
        messages.success(self.request, "Created %s (%s)" %
            (form.instance, form.instance.parent))
        return super(CategoryCreate, self).form_valid(form)


class VendorList(generic.ListView):
    model = Vendor


class VendorCreate(PermissionRequiredMixin, generic.edit.CreateView):
    permission_required = 'grain.can_create_vendor'
    model = Vendor
    fields = ['name']
    success_url = reverse_lazy('grain:vendor_list')


class ProductList(UserPassesTestMixin, generic.ListView):
    login_url = reverse_lazy("grain:profile_list")

    def test_func(self):
        return 'grain_active_user_profile' in self.request.session

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
    form_class = ProductForm
    success_url = reverse_lazy('grain:product_list')

    def get_form_kwargs(self):
        kwargs = super(ProductCreate, self).get_form_kwargs()
        kwargs['currency'] = get_profile(self.request.session).currency
        return kwargs

    def form_valid(self, form):
        profile = get_profile(self.request.session)

        # FIXME: this belongs in form.clean()
        if form.instance.price.currency.code != profile.currency:
            raise ValidationError("Must use same currency as profile")
        if "_add_another" in self.request.POST:
            self.success_url = reverse('grain:product_create')
        messages.success(self.request, "Created %s (%s)" %
            (form.instance, form.instance.price))
        return super(ProductCreate, self).form_valid(form)


def ticket_create(request):
    if 'grain_active_user_profile' not in request.session:
        raise PermissionDenied("Must select profile")

    profile = get_profile(request.session)
    form = TicketForm(profile.pk, request.POST)
    if not form.is_valid():
        raise ValidationError("Invalid form", code='invalid')

    if form.cleaned_data['dish'].meal.owner != profile:
        raise PermissionDenied
    Ticket.objects.create_ticket(
        form.cleaned_data['ingredient'],
        form.cleaned_data['units_used'],
        form.cleaned_data['dish'],
        profile.currency,
        form.cleaned_data['exhausted'],
    )
    return HttpResponseRedirect(reverse("grain:meal_detail",
        args=[form.cleaned_data['dish'].meal.pk]))


class TicketDelete(UserPassesTestMixin, generic.edit.DeleteView):
    login_url = reverse_lazy("grain:profile_list")

    def test_func(self):
        return 'grain_active_user_profile' in self.request.session

    def get_queryset(self):
        return Ticket.objects.filter(ingredient__owner__pk=
            self.request.session['grain_active_user_profile'])

    def get_success_url(self):
        return reverse('grain:ingredient_detail',
                       args=[self.object.ingredient.pk])
