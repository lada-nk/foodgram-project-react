import base64
import datetime as dt

import webcolors
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
# from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import IntegrityError
from rest_framework import serializers

from food.constants import (
    USERNAME_MAX_LENGTH, EMAIL_MAX_LENGTH,
    FIRST_NAME_MAX_LENGTH, LAST_NAME_MAX_LENGTH,
    PASSWORD_MAX_LENGTH
)
# from reviews.models import Category, Genre, Title, Review, Comment
from food.validators import forbidden_usernames

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'role', 'password',
            'image'
        )

    def validate_username(self, value):
        return forbidden_usernames(value)


class UserInfoSerializer(UserSerializer):

    class Meta(UserSerializer.Meta):
        read_only_fields = ('role',)


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
        max_length=PASSWORD_MAX_LENGTH, required=True)

    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data['email']
        try:
            user, created = User.objects.get_or_create(
                username=username, email=email)
            return user
        except IntegrityError:
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError(
                    {'username': [f'username {username} уже занят']},
                    code='duplicate_username')
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError(
                    {'email': [f'email {email} уже занят']},
                    code='duplicate_email'
                )

    def validate_username(self, value):
        return forbidden_usernames(value)


class TokenObtainSerializer(serializers.Serializer):
    email = serializers.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        required=True
    )
    password = serializers.CharField(required=True)
