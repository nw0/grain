from django.conf.urls import url

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

    url(r'^profiles/(?P<pk>\d+)/$',
        views.profile_select,
        name="profile_select"),

    url(r'^cal/(?P<year>[0-9]{4})/(?P<month>[0-9]+)/$',
        views.MealMonthArchive.as_view(month_format='%m'),
        name="calendar"),

    url(r'^meal/(?P<pk>\d+)/$',
        views.MealDetail.as_view(),
        name="meal_detail"),

    url(r'^unit/$',
        views.UnitList.as_view(),
        name="unit_list"),

    url(r'^unit/create/$',
        views.UnitCreate.as_view(),
        name="unit_create"),

    url(r'^category/$',
        views.CategoryList.as_view(),
        name="category_list"),

    url(r'^category/create/$',
        views.CategoryCreate.as_view(),
        name="category_create"),

    url(r'^product/$',
        views.ProductList.as_view(),
        name="product_list"),

    url(r'^product/create/$',
        views.ProductCreate.as_view(),
        name="product_create"),
]
