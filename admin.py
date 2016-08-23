from django.contrib import admin

from .models import (Dish, Ingredient, IngredientCategory, Meal, Product,
                     Ticket, Unit, UserProfile)

admin.site.register(UserProfile)
admin.site.register(Unit)
admin.site.register(IngredientCategory)
admin.site.register(Product)
admin.site.register(Meal)
admin.site.register(Dish)
admin.site.register(Ingredient)
admin.site.register(Ticket)
