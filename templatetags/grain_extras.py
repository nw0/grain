from datetime import timedelta

from django import template

register = template.Library()


@register.inclusion_tag('grain/cal/calendar.html')
def calendar(month, meals):
    rows = []
    current_day = month - timedelta(days=month.weekday())
    month_end = False
    meals, meal_it = meals.order_by('time'), 0
    meal_count = len(meals)

    while not month_end:
        week = []
        for d in range(1, 8):
            day = { 'day_of_week': str(d),
                    'inmonth': current_day.month == month.month,
                    'date_str': current_day.strftime("%Y-%m-%d"),
                    'day': current_day.day }

            while (meal_it < meal_count and
                   current_day == meals[meal_it].time.date()):
                if 'content' not in day:
                    day['content'] = ""
                day['content'] += meals[meal_it].get_meal_type_display()
                meal_it += 1

            current_day += timedelta(days=1)
            week.append(day)

        rows.append(week)
        if current_day.weekday() == 0 and current_day.month > month.month:
            month_end = True

    return {'month': month, 'rows': rows}


@register.inclusion_tag('grain/cal/cell.html')
def cal_cell(cell):
    return {'cell': cell}
