from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe

User = get_user_model()


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов по названию."""

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """Фильтр длярецептов по тэгам, авторам, избранному и корзине."""

    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(favorite__user_id=self.request.user.id)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(customer__user_id=self.request.user.id)
        return queryset

    class Meta:
        model = Recipe
        fields = ('tags', 'author')
