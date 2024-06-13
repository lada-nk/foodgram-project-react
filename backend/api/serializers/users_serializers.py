from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator
from api.utils import create_queryset_obj
from recipes.models import (
    IngredientAmount, Ingredient, Favorite, Recipe, ShoppingCart, Tag)
from users.constants import USERNAME_MAX_LENGTH
from users.models import Follow

User = get_user_model()


class RegistrationSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователей."""

    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())])

    class Meta:
        model = User
        fields = (
            'email', 'id', 'password', 'username', 'first_name', 'last_name')
        extra_kwargs = {
            'email': {'required': True}, 'username': {'required': True},
            'password': {'required': True}, 'first_name': {'required': True},
            'last_name': {'required': True}, }


class UserSerializer(UserSerializer):
    """Сериализатор для пользователей."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'id', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return Follow.objects.filter(
            user_id=user.id, following=get_object_or_404(
                User, id=obj.id)).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватаров."""

    avatar = Base64ImageField(required=True, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeShortSerializer(serializers.Serializer):
    """Сериализатор для рецептов в подписках, избранном, корзине."""

    id = serializers.IntegerField(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    name = serializers.CharField(read_only=True)
    cooking_time = serializers.IntegerField(read_only=True)

    def create(self, validated_data):
        return create_queryset_obj(self)


class FollowSerializer(UserSerializer):
    """Сериализатор для подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'avatar', 'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'avatar')
    
    def create(self, validated_data):
        try:
            return create_queryset_obj(self)
        except IntegrityError as err:
            raise ValidationError(
                {'errors': 'Вы не можете быть подписаны на самого себя'},
                code='id_errors')  from err

    def get_recipes(self, obj):
        queryset = obj.recipe_set.all()
        recipes_limit = self.context['request'].GET.get('recipes_limit')
        if recipes_limit:
            queryset = queryset[:int(recipes_limit)]
        return RecipeShortSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipe_set.all().count()


class DeleteSerializer(serializers.Serializer):
    """Сериализатор для обработки ошибок при удалении объекта."""

    def validate(self, data):
        if self.context['delete_obj'] == 0:
            raise ValidationError({
                'errors': 'Не существует.'}, code='del_not_add_errors')
        return data
