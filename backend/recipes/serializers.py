from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from recipes.models import (
    IngredientAmount, Ingredient, Favorite, Recipe, ShoppingCart, Tag)
from users.serializers import UserSerializer

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
    """Сериализатор для рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(
        source='ingredients_amounts', many=True, read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    image = Base64ImageField(required=True, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time')

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=user, recipe=get_object_or_404(
                    Recipe, id=obj.id)).exists()
        return False

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Favorite.objects.filter(
                user=user, recipe=get_object_or_404(
                    Recipe, id=obj.id)).exists()
        return False

    def validate(self, data):
        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Поле tags обязательное'}, code='no_tags')
        if tags == []:
            raise serializers.ValidationError(
                {'tags': 'Добавьте теги'}, code='empty_tags')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Дублирование тэгов'},
                code='dublicate_tags')
        for tag_id in tags:
            if not Tag.objects.filter(id=tag_id).exists():
                raise serializers.ValidationError(
                    {'ingredients': f'Тэга с id={tag_id} не существует'},
                    code='non_exsisting_tags')
        if not self.initial_data.get('image'):
            raise serializers.ValidationError(
                {'image': 'Добавьте изображение'}, code='empty_image')
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': f'Для рецепта {self.initial_data.get("name")}'
                f' нужны ингредиенты'}, code='no_ingredients')
        ingredients_id = [ingredient["id"] for ingredient in ingredients]
        if len(ingredients_id) != len(set(ingredients_id)):
            raise serializers.ValidationError(
                {'ingredients': 'Дублирование ингридиентов'},
                code='dublicate_ingredients')
        for ingredient_item in ingredients:
            ingredient = Ingredient.objects.filter(id=ingredient_item['id'])
            if not ingredient.exists():
                raise serializers.ValidationError(
                    {'ingredients': f'Ингридиента с id={ingredient_item["id"]}'
                     f' не существует'},
                    code='non_exsisting_ingredients')
            if int(ingredient_item['amount']) < 1:
                raise serializers.ValidationError({
                    'ingredients': 'Количество ингридиента меньше 1'},
                    code='min_ingredients')
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

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        instance.tags.clear()
        instance.tags.set(self.initial_data.get('tags'))
        IngredientAmount.objects.filter(recipe=instance).all().delete()
        self.create_ingredients(validated_data.get('ingredients'), instance)
        instance.save()
        return instance


class RecipeShortLinkSerializer(serializers.ModelSerializer):
    """Сериализатор для короткой ссылки на рецепт"""

    short_link = serializers.SerializerMethodField(
        'get_short_link', read_only=True)

    class Meta:
        model = Recipe
        fields = ('short_link',)

    def get_short_link(self, obj):
        if obj:
            # url = 'https://foodgram-ladank.sytes.net/recipes/'
            return obj.id
        return None
