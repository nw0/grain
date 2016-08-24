from datetime import date

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic

from .models import Meal


def cal_redirect(request):
    return HttpResponseRedirect(reverse('grain:calendar',
                                kwargs={'year': date.today().strftime("%Y"),
                                        'month': date.today().strftime("%m")}))


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
        context['cost_pc_closed'] = 100 * self.object.cost_closed \
                                        / context['cost_total']
        context['cost_pc_open'] = 100 * self.object.cost_open \
                                      / context['cost_total']
        return context
