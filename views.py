from datetime import date

from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import generic

from .models import IngredientCategory, Meal, Product, Unit, UserProfile


def cal_redirect(request):
    if not request.session.get('grain:active_user_profile'):
        return HttpResponseRedirect(reverse('grain:profile_list'))
    return HttpResponseRedirect(reverse('grain:calendar',
                                kwargs={'year': date.today().strftime("%Y"),
                                        'month': date.today().strftime("%m")}))


class ProfileList(generic.ListView):
    model = UserProfile


def profile_select(request, pk):
    request.session['grain:active_user_profile'] \
        = get_object_or_404(UserProfile, pk=pk).pk
    return HttpResponseRedirect(reverse('grain:index'))


class MealMonthArchive(generic.dates.MonthArchiveView):
    queryset = Meal.objects.all()   # FIXME: only show current UserProfile
    date_field = "time"
    allow_future = True


class MealDetail(generic.DetailView):
    model = Meal
    # FIXME: check UserProfile

    def get_context_data(self, **kwargs):
        context = super(MealDetail, self).get_context_data(**kwargs)
        context['cost_total'] = self.object.cost_closed + self.object.cost_open
        if context['cost_total']:
            context['cost_pc_closed'] = 100 * self.object.cost_closed \
                                            / context['cost_total']
            context['cost_pc_open'] = 100 * self.object.cost_open \
                                          / context['cost_total']
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
    model = Product


class ProductCreate(generic.edit.CreateView):
    model = Product
    fields = ['category', 'name', 'units', 'amount', 'fixed', 'price']
    success_url = reverse_lazy('grain:product_list')
