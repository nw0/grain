from datetime import timedelta, date

from django import template

register = template.Library()
BASELINE_MAX = 4    # FIXME: magic: default max meal cost (progress bar)


@register.inclusion_tag('grain/cal/calendar.html')
def calendar(month, meals):
    weeks = []
    current_day = month - timedelta(days=month.weekday())
    meals, meal_it, meal_count = meals.order_by('time'), 0, len(meals)

    while current_day.month <= month.month:
        week = []
        for d in range(1, 8):
            day = {
                'day_of_week': str(d),
                'inmonth': current_day.month == month.month,
                'date': current_day,
                'today': current_day == date.today(),
                'meals': [],
            }

            while (meal_it < meal_count and
                   current_day == meals[meal_it].time.date()):
                meal = meals[meal_it]
                day['meals'].append({
                    'meal': meal,
                    'close_pc': 100 * meal.cost_closed.amount / BASELINE_MAX,
                    'open_pc': 100 * meal.cost_open.amount / BASELINE_MAX,
                    # TODO: consider bar UX for total_price = 0
                    'total_price': meal.cost_closed + meal.cost_open,
                    })
                meal_it += 1

            current_day += timedelta(days=1)
            week.append(day)
        weeks.append(week)
    return {'month': month, 'weeks': weeks}


@register.inclusion_tag('grain/cal/cell.html')
def cal_cell(cell):
    return {'cell': cell}
