from django.contrib import admin
from django.db.models import Count

from .models import (
    Ingredient, IngredientAmount, Favorite, Recipe, Tag, ShoppingCart)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'get_favorite_count')
    list_filter = ('tags__title')
    search_fields = ('name', 'author__username', 'author__id')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(favorite_count=Count('favored_by'))

    @staticmethod
    def get_favorite_count(obj):
        return obj.favorite_count


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('^name',)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientAmount)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
