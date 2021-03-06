from datetime import date, timedelta

from django import template
from django.shortcuts import get_object_or_404

from grain.models import UserProfile

register = template.Library()
BASELINE_MAX = 4    # FIXME: magic: default max meal cost (progress bar)


@register.inclusion_tag('grain/cal/calendar.html')
def calendar(month, meals):
    weeks = []
    # Get the first listed day
    current_day = month - timedelta(days=month.weekday())
    meals, meal_it, meal_count = meals.order_by('time'), 0, len(meals)
    next_month = date(month.year if month.month < 12 else month.year + 1, month.month + 1 if month.month < 12 else 1, 1)

    while meal_count > 0 and meals[meal_it].time.date() < current_day:
        meal_it += 1

    while current_day < next_month:
        week = []
        for d in range(1, 8):
            day = {
                'day_of_week': str(d),
                'inmonth': current_day.month == month.month,
                'date': current_day,
                'today': current_day == date.today(),
                'meals': {},
            }

            while (meal_it < meal_count and
                   current_day == meals[meal_it].time.date()):
                meal = meals[meal_it]
                if meal.meal_type not in day['meals']:
                    day['meals'][meal.meal_type] = {
                        'display': meal.get_meal_type_display(),
                        'close_pc': 0,
                        'open_pc': 0,
                        'total_price': 0,
                        'meal_list': [],
                    }
                day['meals'][meal.meal_type]['total_price'] += meal.cost_closed\
                                                             + meal.cost_open
                day['meals'][meal.meal_type]['close_pc'] += 100 / BASELINE_MAX \
                    * float(meal.cost_closed.amount)
                day['meals'][meal.meal_type]['open_pc'] += 100 / BASELINE_MAX \
                    * float(meal.cost_open.amount)
                day['meals'][meal.meal_type]['meal_list'].append(meal)
                meal_it += 1

            current_day += timedelta(days=1)
            week.append(day)
        weeks.append(week)
    return {'month': month, 'weeks': weeks}


@register.inclusion_tag('grain/cal/cell.html')
def cal_cell(day):
    return {'cell': day}


@register.inclusion_tag('grain/embeds/dish_list_embed.html')
def dish_list(request, meal):
    return {
        'dishes': meal.dish_set.order_by('-cost_closed', '-cost_open', 'id'),
        'request': request }


@register.inclusion_tag('grain/embeds/cat_list_li.html')
def cat_list(categories):
    return {'cats': categories}


@register.simple_tag
def get_profile_name(pk):
    if pk:
        return get_object_or_404(UserProfile, pk=pk).note
    return "No profile selected"


@register.inclusion_tag('grain/embeds/profile_list_nav.html')
def get_profile_list(user):
    return {'profiles': UserProfile.objects.filter(user=user).order_by('pk')}


@register.inclusion_tag('grain/embeds/ingredient_form_embed.html')
def ingredient_form_bootstrap(request, dish):
    return {'form':
        dish.get_ticket_form(request.session.get('grain_active_user_profile'))}
