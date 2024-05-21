import base64

from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from rest_framework import serializers

from recipes.models import Recipie, Tag, Ingredient
from users.serializers import UserSerializer


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipieSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientSerializer(read_only=True, many=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipie
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time')

    def get_is_in_shopping_cart(self, obj):
        return True

    def get_is_favorited(self, obj):
        return True
