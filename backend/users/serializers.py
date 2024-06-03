import base64
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from rest_framework import serializers

from users.constants import (
    USERNAME_MAX_LENGTH, EMAIL_MAX_LENGTH,
    FIRST_NAME_MAX_LENGTH, LAST_NAME_MAX_LENGTH,
    PASSWORD_MAX_LENGTH)
from recipes.models import Recipe
from users.models import Follow
from users.validators import forbidden_usernames


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
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
    avatar = Base64ImageField(required=True, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        max_length=PASSWORD_MAX_LENGTH, required=True)
    new_password = serializers.CharField(
        max_length=PASSWORD_MAX_LENGTH, required=True)


class RegistrationSerializer(serializers.Serializer):
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
    id = serializers.IntegerField(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    name = serializers.CharField(read_only=True)
    cooking_time = serializers.IntegerField(read_only=True)


class FollowSerializer(serializers.ModelSerializer):
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
