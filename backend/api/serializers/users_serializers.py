from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator
from recipes.models import Favorite, ShoppingCart
from users.models import Follow

User = get_user_model()


class CreateQuerysetObjMixin:
    """Миксин для добавления объекта в Queryset."""

    def create_queryset_obj(self, name_object, select_object, queryset):
        user = self.context['request'].user
        queryset_obj, created = queryset.get_or_create(
            user=user, **{name_object: select_object})
        if created:
            return select_object
        raise ValidationError(
            {'errors': 'Уже существует.'}, code='dublicate_errors')


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
        return user.is_authenticated and user.follower.filter(
            following=get_object_or_404(User, id=obj.id)).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватаров."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeShortBaseSerializer(serializers.Serializer,
                                CreateQuerysetObjMixin):
    """Сериализатор для рецептов в подписках, избранном, корзине."""

    id = serializers.IntegerField(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    name = serializers.CharField(read_only=True)
    cooking_time = serializers.IntegerField(read_only=True)


class RecipeShortFavoriteSerializer(RecipeShortBaseSerializer):
    """Сериализатор для рецептов в подписках, избранном, корзине."""

    def create(self, validated_data):
        return self.create_queryset_obj(
            'recipe', validated_data.pop('select_object'),
            Favorite.objects.all())


class RecipeShortShoppingCartSerializer(RecipeShortBaseSerializer):
    """Сериализатор для рецептов в подписках, избранном, корзине."""

    def create(self, validated_data):
        return self.create_queryset_obj(
            'recipe', validated_data.pop('select_object'),
            ShoppingCart.objects.all())


class FollowSerializer(UserSerializer, CreateQuerysetObjMixin):
    """Сериализатор для подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'avatar', 'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'avatar')

    def create(self, validated_data):
        return self.create_queryset_obj(
            'following', validated_data.pop('select_object'),
            Follow.objects.all())

    def get_recipes(self, obj):
        queryset = obj.recipe_set.all()
        recipes_limit = self.context['request'].GET.get('recipes_limit')
        if recipes_limit:
            queryset = queryset[:int(recipes_limit)]
        return RecipeShortBaseSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipe_set.all().count()
