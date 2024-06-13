from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from recipes.models import (
    IngredientAmount, Ingredient, Favorite, Recipe, ShoppingCart, Tag)

from .users_serializers import UserSerializer

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингридиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор для ингридиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.CharField(read_only=True,
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(min_value=1, required=True)

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')
        validators = [
            UniqueTogetherValidator(
                queryset=IngredientAmount.objects.all(),
                fields=('ingredient', 'recipe'))]


class RecipieSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(
        source='ingredients_amounts', many=True, read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    image = Base64ImageField(required=True, allow_null=False)
    cooking_time = serializers.IntegerField(min_value=1, max_value=1440)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time')

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return ShoppingCart.objects.filter(
            user_id=user.id, recipe=get_object_or_404(
                Recipe, id=obj.id)).exists()


    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return Favorite.objects.filter(
            user_id=user.id, recipe=get_object_or_404(
                Recipe, id=obj.id)).exists()

    def validate(self, data):
        self.validate_tags(self.initial_data.get('tags'))
        ingredients = self.initial_data.get('ingredients')
        data['ingredients'] = self.validate_ingredients(ingredients)
        return data
    
    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError({
                'ingredients': 'Для рецепта нужны ингредиенты'},
                code='no_ingredients')
        ingredients_id = [ingredient.get('id') for ingredient in value]
        len_ingredients_id = len(ingredients_id)
        if len_ingredients_id != len(set(ingredients_id)):
            raise serializers.ValidationError(
                {'ingredients': 'Дублирование ингридиентов'},
                code='dublicate_ingredients')
        ingredients_exist = Ingredient.objects.in_bulk(ingredients_id)
        if len_ingredients_id != len(ingredients_exist.keys()):
            raise serializers.ValidationError(
                {'ingredients': f'Несуществующий ингридиент'},
                code='non_exsisting_ingredients')
        return value
    
    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                {'tags': 'Поле tags обязательное'}, code='no_tags')
        len_value = len(value)
        if len_value != len(set(value)):
            raise serializers.ValidationError(
                {'tags': 'Дублирование тэгов'},
                code='dublicate_tags')
        tags = Tag.objects.in_bulk(value)
        if len_value != len(tags.keys()):
            raise serializers.ValidationError(
                {'ingredients': f'Несуществующий тэг'}, code='non_exsisting_tags')
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                {'image': 'Добавьте изображение'}, code='empty_image')
        return value

    def create_ingredients(self, ingredients, recipe):
        ingredients_list = [IngredientAmount(
            recipe=recipe, ingredient_id=ingredient.get('id'),
            amount=ingredient.get('amount')) for ingredient in ingredients]
        IngredientAmount.objects.bulk_create(ingredients_list)

    def create(self, validated_data):
        image = validated_data.pop('image')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            image=image, author=self.context['request'].user, **validated_data)
        recipe.tags.set(self.initial_data.get('tags'))
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        instance.tags.clear()
        instance.tags.set(self.initial_data.get('tags'))
        instance.ingredients_amounts.all().delete()
        self.create_ingredients(validated_data.get('ingredients'), instance)
        instance.save()
        return instance
