import pyshorteners
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import ModelViewSet

from .serializers import (RecipieSerializer, IngredientSerializer,
                          TagSerializer, RecipeShortLinkSerializer)
from users.serializers import RecipeShortSerializer
from .permissions import IsAuthorOrReadOnly
from .models import Recipe, Ingredient, Tag, Favorite, ShoppingCart
from .filters import IngredientFilter, RecipeFilter

User = get_user_model()


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    serializer_class = RecipieSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    # def get_queryset(self):
    #     queryset = Recipe.objects.all()
    #     is_favorited = self.request.query_params.get('is_favorited')
    #     is_in_shopping_cart = self.request.query_params.get(
    #         'is_in_shopping_cart')
    #     # if is_favorited is not None:
    #     #     queryset = queryset
    #     if is_in_shopping_cart is not None:
    #         queryset = self.request.user.shopping_cart.all()
    #         queryset = Recipe.objects.all()
    #     return queryset

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, pk):
        user = request.user
        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=pk)
            favorite = Favorite.objects.filter(user=user, recipe=recipe)
            if favorite.exists():
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            raise ValidationError({
                'errors': f'Вы не добавили рецепт {recipe.name} в избранное.'},
                code='not_favorite_errors')
        recipe = Recipe.objects.filter(id=pk)
        if not recipe.exists():
            raise ValidationError(
                {'errors': 'Рецепта не существует.'},
                code='no_recipe_errors')
        recipe = recipe.first()
        serializer = RecipeShortSerializer(recipe)
        favorite, created = Favorite.objects.get_or_create(
            user=user, recipe=recipe)
        if created:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        raise ValidationError({
            'errors': f'Вы уже добавили рецепт {recipe.name} в избранное.'},
            code='dublicate_errors')

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,))
    def shopping_cart(self, request, pk):
        user = request.user
        if request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=pk)
            shopping_cart = ShoppingCart.objects.filter(user=user, recipe=recipe)
            if shopping_cart.exists():
                shopping_cart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            raise ValidationError({
                'errors': f'Вы не добавили рецепт {recipe.name} в корзину.'},
                code='not_favorite_errors')
        recipe = Recipe.objects.filter(id=pk)
        if not recipe.exists():
            raise ValidationError(
                {'errors': 'Рецепта не существует.'},
                code='no_recipe_errors')
        recipe = recipe.first()
        serializer = RecipeShortSerializer(recipe)
        shopping_cart, created = ShoppingCart.objects.get_or_create(
            user=user, recipe=recipe)
        if created:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        raise ValidationError({
            'errors': f'Вы уже добавили рецепт {recipe.name} в корзину.'},
            code='dublicate_errors')

    @action(detail=True, methods=['get'],
            permission_classes=(permissions.AllowAny,),
            url_path='get-link')
    def get_link(self, request, pk):
        recipe = Recipe.objects.filter(id=pk)
        recipe = recipe.first()
        serializer = RecipeShortLinkSerializer(
            recipe, context={'request': request})
        return Response(
            {'short-link': serializer.data['short_link']},
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
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    http_method_names = ['get']
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ['get']
    filter_backends = (DjangoFilterBackend,)
    pagination_class = None
