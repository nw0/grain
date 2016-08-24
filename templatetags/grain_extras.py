from django import template
from django.core.urlresolvers import reverse

register = template.Library()


@register.inclusion_tag('grain/cal/calendar.html')
def calendar():
    week1 = [
        {   'day_of_week': "1",
            'inmonth': False,
            'date_str': "2013-02-24",
            'day': "24" },
        {   'day_of_week': "2",
            'inmonth': False,
            'date_str': "2013-02-25",
            'day': "25" },
        {   'day_of_week': "3",
            'inmonth': False,
            'date_str': "2013-02-26",
            'day': "26" },
        {   'day_of_week': "4",
            'inmonth': False,
            'date_str': "2013-02-27",
            'day': "27" },
        {   'day_of_week': "5",
            'inmonth': False,
            'date_str': "2013-02-28",
            'day': "28" },
        {   'day_of_week': "6",
            'inmonth': True,
            'date_str': "2013-03-01",
            'day': "1" },
        {   'day_of_week': "7",
            'inmonth': True,
            'date_str': "2013-03-02",
            'day': "2" }
    ]
    return {'rows': [week1, []]}

@register.inclusion_tag('grain/cal/cell.html')
def cal_cell(cell):
    return {'cell': cell}
