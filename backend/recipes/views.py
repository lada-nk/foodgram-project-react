from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, status
# from rest_framework.decorators import action, api_view
# from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet, ModelViewSet
# from rest_framework.mixins import (
#     CreateModelMixin, ListModelMixin, DestroyModelMixin, RetrieveModelMixin
# )

from .serializers import (RecipieSerializer, IngredientSerializer,
                          TagSerializer)
# from .permissions import UserRegistration
from .models import Recipe, Ingredient, Tag
from .filters import IngredientFilter

User = get_user_model()


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    # permission_classes = (UserRegistration,)
    serializer_class = RecipieSerializer
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


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
