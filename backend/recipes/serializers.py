from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from drf_extra_fields.fields import Base64ImageField

from recipes.models import Recipe, Tag, Ingredient, IngredientAmount
from users.serializers import UserSerializer


User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')


    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')
        validators = [
            UniqueTogetherValidator(
                queryset=IngredientAmount.objects.all(),
                fields=['ingredient', 'recipe'])]


class RecipieSerializer(serializers.ModelSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(
        source='ingredientamount_set', many=True, read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time')

    def get_is_in_shopping_cart(self, obj):
        return True

    def get_is_favorited(self, obj):
        return True
    
    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': f'Для рецепта {self.initial_data.get("name")} нужны ингредиенты'})
        ingredients_list = []
        for ingredient_item in ingredients:
            ingredient = get_object_or_404(Ingredient,
                                           id=ingredient_item['id'])
            if ingredient in ingredients_list:
                raise serializers.ValidationError(
                    f'Ингридиент {ingredient.name} уже добавлен')
            if int(ingredient_item['amount']) < 1:
                raise serializers.ValidationError({
                    'ingredients': (
                        f'Минимальное количество ингредиента {ingredient.name} - 1{ingredient.measurement_unit}')
                    })
            ingredients_list.append(ingredient)
        data['ingredients'] = ingredients
        return data

    def validate_cooking_time(self, value):
        if value > 1440 or value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть в интервале 1-1440 минут')
        return value

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            IngredientAmount.objects.create(
                recipe=recipe, ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'))

    def create(self, validated_data):
        image = validated_data.pop('image')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(image=image, **validated_data)
        recipe.tags.set(self.initial_data.get('tags'))
        self.create_ingredients(ingredients, recipe)
        return recipe