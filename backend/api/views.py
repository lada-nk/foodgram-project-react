import pyshorteners
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSetMixin
from recipes.models import Ingredient, Favorite, Recipe, ShoppingCart, Tag
from users.models import Follow
from foodgram_backend.settings import BASE_SHORT_RECIPE_URL

from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers.recipes_serializers import (
    IngredientSerializer, RecipieSerializer, TagSerializer)
from .serializers.users_serializers import (
    AvatarSerializer, DeleteSerializer, FollowSerializer,
    RecipeShortSerializer, UserSerializer)

User = get_user_model()


class SelectObjectMixin(ViewSetMixin):
    """"Добавление/удаление в queryset."""

    def add_delete_to_queryset(self, queryset, name_object, request, pk):
        user = request.user
        select_object = self.get_object()
        if request.method == 'DELETE':
            delete_obj, delete = queryset.filter(user=user,
                **{name_object: select_object}).delete()
            serializer = DeleteSerializer(
                data=request.data, context={'delete_obj': delete_obj})
            serializer.is_valid(raise_exception=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = self.get_serializer(data=request.data,
            context={'request': request, 'select_object': select_object,
                    'queryset':queryset, 'name_object': name_object})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RecipeViewSet(ModelViewSet, SelectObjectMixin):
    """Вьюсет для рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    serializer_class = RecipieSerializer
    pagination_class = LimitPageNumberPagination
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filterset_class = RecipeFilter


    @action(detail=True, methods=('post', 'delete'),
            permission_classes=(permissions.IsAuthenticated,),
            serializer_class = RecipeShortSerializer)
    def favorite(self, request, pk):
        return self.add_delete_to_queryset(
            Favorite.objects.all(), 'recipe', request, pk)

    @action(detail=True, methods=('post', 'delete'),
            permission_classes=(permissions.IsAuthenticated,),
            serializer_class = RecipeShortSerializer)
    def shopping_cart(self, request, pk):
        return self.add_delete_to_queryset(
            ShoppingCart.objects.all(), 'recipe', request, pk)

    @action(detail=True,
            permission_classes=(permissions.AllowAny,),
            url_path='get-link')
    def get_link(self, request, pk):
        url = str(BASE_SHORT_RECIPE_URL) + str(pk)
        return Response(
            {'short-link': pyshorteners.Shortener().tinyurl.short(url)})

    @action(detail=False,
            permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request, pk=None):
        name = 'recipe__ingredients__name'
        measurement_unit = 'recipe__ingredients__measurement_unit'
        amount = 'recipe__ingredients_amounts__amount'
        ingredients = request.user.customer.select_related(
            'recipe').order_by(name).values(
                name, measurement_unit).annotate(amount=Sum(amount)).all()
        if not ingredients:
            raise ValidationError(
                {'ingredients': 'Для покупок нужны ингредиенты'},
                code='no_ingredients')
        text = 'Список покупок:\n\n'
        for number, ingredient in enumerate(ingredients, start=1):
            amount = ingredient.get('amount')
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
    http_method_names = ('get',)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class TagViewSet(ModelViewSet):
    """Вьюсет для тэгов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    http_method_names = ('get',)
    filter_backends = (DjangoFilterBackend,)
    pagination_class = None


class UserViewSet(UserViewSet, SelectObjectMixin):
    """Вьюсет для пользователей."""

    pagination_class = LimitPageNumberPagination

    @action(detail=False,
            permission_classes=(permissions.IsAuthenticated,),
            serializer_class=UserSerializer, url_path='me')
    def me(self, request, pk=None):
        return Response(self.get_serializer(request.user).data)

    @action(detail=False, methods=('put', 'patch', 'delete'),
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

    @action(detail=True, methods=('post', 'delete'),
            serializer_class=FollowSerializer,
            permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, id):
        return self.add_delete_to_queryset(
            Follow.objects.all(), 'following', request, id)

    @action(detail=False, serializer_class=FollowSerializer,
            permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request, pk=None):
        serializer = self.get_serializer(
            self.paginate_queryset(
                [follow.following for follow in request.user.follower.all()]),
            many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
