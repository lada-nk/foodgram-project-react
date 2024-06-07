import pyshorteners
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from users.serializers import RecipeShortSerializer

from .filters import IngredientFilter, RecipeFilter
from .models import Ingredient, Favorite, Recipe, ShoppingCart, Tag
from .permissions import IsAuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipieSerializer,
                          RecipeShortLinkSerializer, TagSerializer)

User = get_user_model()


class RecipeViewSet(ModelViewSet):
    """Вьюсет для рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    serializer_class = RecipieSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def favorite_shopping_cart(self, queryset, request, pk):
        """"Добавление/удаление рецепта в избранное/корзину"""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if queryset == Favorite.objects.all():
            model_name = 'избранное'
        model_name = 'корзину'
        if request.method == 'DELETE':
            favorite = queryset.filter(user=user, recipe=recipe)
            if favorite.exists():
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            raise ValidationError({
                'errors': f'Вы не добавили рецепт {recipe.name}'
                f' в {model_name}.'},
                code='del_not_add_errors')
        serializer = RecipeShortSerializer(recipe)
        favorite, created = queryset.get_or_create(
            user=user, recipe=recipe)
        if created:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        raise ValidationError({
            'errors': f'Вы уже добавили рецепт {recipe.name} в {model_name}.'},
            code='dublicate_errors')

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, pk):
        return self.favorite_shopping_cart(Favorite.objects.all(), request, pk)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,))
    def shopping_cart(self, request, pk):
        return self.favorite_shopping_cart(
            ShoppingCart.objects.all(), request, pk)

    @action(detail=True, methods=['get'],
            permission_classes=(permissions.AllowAny,),
            url_path='get-link')
    def get_link(self, request, pk):
        url = str('http://foodgram-ladank.sytes.net/recipes/') + str(pk)
        return Response(
            {'short-link': format(pyshorteners.Shortener().clckru.short(url))},
            status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'],
            permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request, pk=None):
        name = 'recipe__ingredients__name'
        measurement_unit = 'recipe__ingredients__measurement_unit'
        amount = 'recipe__ingredients_amounts__amount'
        ingredients = request.user.shopping_cart.select_related(
            'recipe').order_by(name).values(
                name, measurement_unit).annotate(amount=Sum(amount)).all()
        if not ingredients:
            raise ValidationError(
                {'ingredients': 'Для покупок нужны ингредиенты'},
                code='no_ingredients')
        text = 'Список покупок:\n\n'
        for number, ingredient in enumerate(ingredients, start=1):
            amount = ingredient['amount']
            text += (
                f'{number}) '
                f'{ingredient[name]} - '
                f'{amount} '
                f'{ingredient[measurement_unit]}\n')
        response = HttpResponse(text, content_type='text/plain')
        filename = 'shopping_cart.txt'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response


class IngredientViewSet(ModelViewSet):
    """Вьюсет для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    http_method_names = ['get']
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class TagViewSet(ModelViewSet):
    """Вьюсет для тэгов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get']
    filter_backends = (DjangoFilterBackend,)
    pagination_class = None
