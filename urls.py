from django.conf.urls import url
from django.views.defaults import page_not_found

from . import views

urlpatterns = [
    url(r'^$',
        views.cal_redirect,
        name="index"),

    url(r'^cal/$',
        views.cal_redirect,
        name="calendar_redirect"),

    url(r'^profiles/$',
        views.ProfileList.as_view(),
        name="profile_list"),

    url(r'^profiles/settings/$',
        views.ProfileUpdate.as_view(),
        name="profile_update"),

    url(r'^profiles/create/$',
        views.ProfileCreate.as_view(),
        name="profile_create"),

    url(r'^profiles/(?P<pk>\d+)/$',
        views.profile_select,
        name="profile_select"),

    url(r'^consumers/$',
        views.ConsumerList.as_view(),
        name="consumer_list"),

    url(r'^consumers/(?P<pk>\d+)/$',
        views.ConsumerDetail.as_view(),
        name="consumer_detail"),

    url(r'^consumers/create/$',
        views.ConsumerCreate.as_view(),
        name="consumer_create"),

    url(r'^calendar/(?P<year>[0-9]{4})/(?P<month>[0-9]+)/$',
        views.MealMonthArchive.as_view(month_format='%m'),
        name="calendar"),

    url(r'^calendar/(?P<year>[0-9]{4})/(?P<month>[0-9]+)/all/$',
        views.MealMonthArchiveFull.as_view(month_format='%m'),
        name="calendar_all"),

    url(r'^meals/date/(?P<year>[0-9]{4})/(?P<month>[0-9]+)/(?P<day>[0-9]+)/$',
        views.MealDayArchive.as_view(month_format='%m'),
        name="meal_day"),

    url(r'^meals/date/(?P<year>[0-9]{4})/(?P<month>[0-9]+)/(?P<day>[0-9]+)/(?P<meal_type>\d+)/$',
        views.MealDayArchiveSpecific.as_view(month_format='%m'),
        name="meal_day_spec"),

    url(r'^meals/(?P<pk>\d+)/$',
        views.MealDetail.as_view(),
        name="meal_detail"),

    url(r'^meals/create/$',
        views.MealCreate.as_view(),
        name="meal_create"),

    url(r'^meals/delete/(?P<pk>\d+)/$',
        views.MealDelete.as_view(),
        name="meal_delete"),

    url(r'^dishes/create/$',
        views.DishCreate.as_view(),
        name="dish_create"),

    url(r'^dishes/delete/(?P<pk>\d+)/$',
        views.DishDelete.as_view(),
        name="dish_delete"),

    url(r'^inventory/$',
        views.IngredientList.as_view(),
        name="inventory"),

    url(r'^inventory/all/$',
        views.IngredientListFull.as_view(),
        name="inventory_all"),

    url(r'^ingredients/(?P<pk>\d+)/$',
        views.IngredientDetail.as_view(),
        name="ingredient_detail"),

    url(r'^ingredient/create/$',
        views.IngredientCreate.as_view(),
        name="ingredient_create"),

    url(r'^units/$',
        views.UnitList.as_view(),
        name="unit_list"),

    url(r'^units/create/$',
        views.UnitCreate.as_view(),
        name="unit_create"),

    url(r'^categories/$',
        views.CategoryList.as_view(),
        name="category_list"),

    url(r'^categories/create/$',
        views.CategoryCreate.as_view(),
        name="category_create"),

    url(r'^vendors/$',
        views.VendorList.as_view(),
        name="vendor_list"),

    url(r'^vendors/create/$',
        views.VendorCreate.as_view(),
        name="vendor_create"),

    url(r'^products/$',
        views.ProductList.as_view(),
        name="product_list"),

    url(r'^products/raw/(?P<pk>\d+)/$',
        views.product_raw,
        name="product_raw"),

    url(r'^products/raw/$',
        page_not_found,     # FIXME
        name="product_raw_noid"),

    url(r'^products/create/$',
        views.ProductCreate.as_view(),
        name="product_create"),

    url(r'^ticket/create/$',
        views.ticket_create,
        name="ticket_create"),

    url(r'^ticket/delete/(?P<pk>\d+)/$',
        views.TicketDelete.as_view(),
        name="ticket_delete"),
]
