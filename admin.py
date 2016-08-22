from django.contrib import admin

from .models import UserProfile, IngredientCategory

admin.site.register(UserProfile)
admin.site.register(IngredientCategory)
