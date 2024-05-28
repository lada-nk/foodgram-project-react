from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Recipe, Tag, Ingredient, IngredientAmount


admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(IngredientAmount)
