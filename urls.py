from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$',
        views.cal_redirect,
        name="index"),

    url(r'^cal/$',
        views.cal_redirect,
        name="calendar_redirect"),

    url(r'^cal/(?P<year>[0-9]{4})/(?P<month>[-\w]+)/$',
        views.MealMonthArchive.as_view(),
        name="calendar"),
]
