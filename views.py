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
    queryset = Meal.objects.all()
    date_field = "time"
    allow_future = True
