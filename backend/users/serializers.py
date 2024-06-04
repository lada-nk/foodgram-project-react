import base64
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField

from users.constants import (
    USERNAME_MAX_LENGTH, EMAIL_MAX_LENGTH,
    FIRST_NAME_MAX_LENGTH, LAST_NAME_MAX_LENGTH,
    PASSWORD_MAX_LENGTH)
from recipes.models import Recipe
from users.models import Follow
from users.validators import forbidden_usernames


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """"Сериализатор для пользователей."""

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

    def validate_username(self, value):
        return forbidden_usernames(value)


class AvatarSerializer(serializers.ModelSerializer):
    """"Сериализатор для аватаров."""

    avatar = Base64ImageField(required=True, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class SetPasswordSerializer(serializers.Serializer):
    """"Сериализатор для пароля."""

    current_password = serializers.CharField(
        max_length=PASSWORD_MAX_LENGTH, required=True)
    new_password = serializers.CharField(
        max_length=PASSWORD_MAX_LENGTH, required=True)


class RegistrationSerializer(serializers.Serializer):
    """"Сериализатор для регистрации пользователя."""

    email = serializers.EmailField(
        max_length=EMAIL_MAX_LENGTH, required=True)
    username = serializers.CharField(
        max_length=USERNAME_MAX_LENGTH, required=True)
    first_name = serializers.CharField(
        max_length=FIRST_NAME_MAX_LENGTH, required=True)
    last_name = serializers.CharField(
        max_length=LAST_NAME_MAX_LENGTH, required=True)
    password = serializers.CharField(
        max_length=PASSWORD_MAX_LENGTH, required=True, write_only=True)
    id = serializers.IntegerField(read_only=True)

    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data['email']
        try:
            user, created = User.objects.get_or_create(
                username=username, email=email, defaults={
                    'first_name': validated_data['first_name'],
                    'last_name': validated_data['last_name'],
                    'password': validated_data['password']})
            return user
        except IntegrityError:
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError(
                    {'username': [f'username {username} уже занят']},
                    code='duplicate_username')
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError(
                    {'email': [f'email {email} уже занят']},
                    code='duplicate_email')

    def validate_username(self, value):
        return forbidden_usernames(value)


class RecipeShortSerializer(serializers.Serializer):
    """"Сериализатор для рецептов в подписках, избранном, корзине."""

    id = serializers.IntegerField(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    name = serializers.CharField(read_only=True)
    cooking_time = serializers.IntegerField(read_only=True)


class FollowSerializer(serializers.ModelSerializer):
    """"Сериализатор для подписок."""

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
