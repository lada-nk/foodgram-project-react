from django.contrib import admin

from .models import Ingredient, IngredientAmount, Recipe, Tag

admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(Ingredient)
admin.site.register(IngredientAmount)
