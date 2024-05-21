from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.pagination import LimitOffsetPagination

from .constants import EMAIL_MAX_LENGTH


User = get_user_model()


class TokenObtainSerializer(serializers.Serializer):
    email = serializers.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        required=True
    )
    password = serializers.CharField(required=True)


class FollowSerializer(serializers.Serializer):
    pagination_class = LimitOffsetPagination

    email = serializers.EmailField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    is_subscribed = serializers.BooleanField(read_only=True)
