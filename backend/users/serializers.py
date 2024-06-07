from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from django.shortcuts import get_object_or_404
from rest_framework.validators import UniqueValidator
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from users.models import Follow
from users.validators import forbidden_usernames
from users.constants import (
    USERNAME_MAX_LENGTH, EMAIL_MAX_LENGTH,
    FIRST_NAME_MAX_LENGTH, LAST_NAME_MAX_LENGTH,
    PASSWORD_MAX_LENGTH
)


User = get_user_model()


class RegistrationSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователей."""

    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())])
    username = serializers.CharField(
        max_length=USERNAME_MAX_LENGTH, required=True,
        validators=[UniqueValidator(queryset=User.objects.all())])

    class Meta:
        model = User
        fields = (
            'email', 'id', 'password', 'username', 'first_name', 'last_name')
        extra_kwargs = {
            'email': {'required': True}, 'username': {'required': True},
            'password': {'required': True}, 'first_name': {'required': True},
            'last_name': {'required': True}, }

    def validate_username(self, value):
        return forbidden_usernames(value)


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
        if user.is_authenticated:
            return Follow.objects.filter(
                user=user, following=get_object_or_404(
                    User, id=obj.id)).exists()
        return False


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


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    id = serializers.ReadOnlyField()
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
    avatar = Base64ImageField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'avatar', 'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        queryset = obj.recipe_set.all()
        recipes_limit = self.context['request'].GET.get('recipes_limit')
        if recipes_limit:
            queryset = queryset[:int(recipes_limit)]
        return RecipeShortSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipe_set.all().count()
