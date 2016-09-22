from django.contrib import admin

from .models import (Consumer, Dish, GrainEvent, Ingredient,
                     IngredientCategory, Meal, Product, Ticket, Unit,
                     UserProfile, Vendor)

admin.site.register(GrainEvent)
admin.site.register(UserProfile)
admin.site.register(Unit)
admin.site.register(Consumer)
admin.site.register(IngredientCategory)
admin.site.register(Vendor)
admin.site.register(Product)
admin.site.register(Meal)
admin.site.register(Dish)
admin.site.register(Ingredient)
admin.site.register(Ticket)
