import pyshorteners
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import (
    ModelViewSet, ViewSetMixin, ReadOnlyModelViewSet)
from recipes.models import Ingredient, Favorite, Recipe, ShoppingCart, Tag
from users.models import Follow

from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers.recipes_serializers import (
    IngredientSerializer, RecipeRequestSerializer,
    RecipeResponseSerializer, TagSerializer)
from .serializers.users_serializers import (
    AvatarSerializer, FollowSerializer,
    RecipeShortFavoriteSerializer, RecipeShortShoppingCartSerializer,
    UserSerializer)

User = get_user_model()


class SelectObjectMixin(ViewSetMixin):
    """"Добавление/удаление в queryset."""

    def add_delete_to_queryset(self, queryset, name_object, request):
        user = request.user
        select_object = self.get_object()
        if request.method == 'DELETE':
            delete_obj, _ = queryset.filter(
                user=user, **{name_object: select_object}).delete()
            if delete_obj == 0:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(select_object=select_object)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RecipeViewSet(ModelViewSet, SelectObjectMixin):
    """Вьюсет для рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = LimitPageNumberPagination
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    filterset_class = RecipeFilter
    serializer_class = RecipeResponseSerializer

    def create(self, request, *args, **kwargs):
        serializer = RecipeRequestSerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        response_serializer = RecipeResponseSerializer(
            instance=serializer.save(), context={'request': request})
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = RecipeRequestSerializer(
            instance, data=request.data,
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        response_serializer = RecipeResponseSerializer(
            instance=serializer.save(), context={'request': request})
        return Response(response_serializer.data)

    @action(detail=True, methods=('post', 'delete'),
            permission_classes=(permissions.IsAuthenticated,),
            serializer_class=RecipeShortFavoriteSerializer)
    def favorite(self, request, pk):
        return self.add_delete_to_queryset(
            Favorite.objects.all(), 'recipe', request)

    @action(detail=True, methods=('post', 'delete'),
            permission_classes=(permissions.IsAuthenticated,),
            serializer_class=RecipeShortShoppingCartSerializer)
    def shopping_cart(self, request, pk):
        return self.add_delete_to_queryset(
            ShoppingCart.objects.all(), 'recipe', request)

    @action(detail=True,
            permission_classes=(permissions.AllowAny,),
            url_path='get-link')
    def get_link(self, request, pk):
        url = f'http://{settings.BASE_SHORT_RECIPE_URL}/recipes/{pk}'
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
            return Response(status=status.HTTP_400_BAD_REQUEST)
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


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для тэгов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
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
        serializer = AvatarSerializer(user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)

    @action(detail=True, methods=('post', 'delete'),
            serializer_class=FollowSerializer,
            permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, id):
        try:
            return self.add_delete_to_queryset(
                Follow.objects.all(), 'following', request)
        except IntegrityError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, serializer_class=FollowSerializer,
            permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request, pk=None):
        serializer = self.get_serializer(
            self.paginate_queryset(
                [follow.following for follow in request.user.follower.all()]),
            many=True)
        return self.get_paginated_response(serializer.data)
