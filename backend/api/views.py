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
from recipes.models import Ingredient, Favorite, Recipe, ShoppingCart, Tag
from users.models import Follow
from users.serializers import RecipeShortSerializer

from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers.recipes_serializers import (IngredientSerializer, RecipieSerializer,
                          TagSerializer)
from .serializers.users_serializers import AvatarSerializer, FollowSerializer, UserSerializer

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
            {'short-link': pyshorteners.Shortener().tinyurl.short(url)},
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


class UserViewSet(UserViewSet):
    """Вьюсет для пользователей."""

    pagination_class = LimitPageNumberPagination

    @action(detail=False, methods=['get'],
            permission_classes=(permissions.IsAuthenticated,),
            serializer_class=UserSerializer, url_path='me')
    def me(self, request, pk=None):
        return Response(self.get_serializer(request.user).data)

    @action(detail=False, methods=['put', 'patch', 'delete'],
            permission_classes=(permissions.IsAuthenticated,),
            url_path='me/avatar')
    def user_avatar(self, request, pk=None):
        user = self.request.user
        if self.request.method == 'DELETE':
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(
            user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, id):
        user = request.user
        following = get_object_or_404(User, id=id)
        if request.method == 'DELETE':
            follow = Follow.objects.filter(user=user, following=following)
            if not follow.exists():
                raise ValidationError(
                    {'errors': f'Вы не подписаны на автора'
                     f' {following.username}.'},
                    code='not_follow_errors')
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if user.id == following.id:
            raise ValidationError(
                {'errors': 'Вы не можете быть подписаны на самого себя'},
                code='id_errors')
        follow, created = Follow.objects.get_or_create(
            user=user, following=following)
        if not created:
            raise ValidationError(
                {'errors': f'Вы уже подписаны на автора {following.username}'},
                code='dublicate_errors')
        serializer = FollowSerializer(
            following, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'],
            permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request, pk=None):
        serializer = FollowSerializer(
            self.paginate_queryset(
                [follow.following for follow in request.user.follower.all()]),
            many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
