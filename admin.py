from django.contrib import admin

from .models import IngredientCategory, Product, Unit, UserProfile

admin.site.register(UserProfile)
admin.site.register(Unit)
admin.site.register(IngredientCategory)
admin.site.register(Product)
