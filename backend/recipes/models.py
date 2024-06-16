from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .constants import (
    INGREDIENT_NAME_MAX_LENGTH, MEASUREMENT_MAX_LENGTH,
    RECIPE_TITLE_MAX_LENGTH, SLUG_MAX_LENGTH, TAG_NAME_MAX_LENGTH)

User = get_user_model()


class Ingredient(models.Model):
    """Модель для ингридиентов."""

    name = models.CharField(
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        verbose_name='Название ингредиента')
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_MAX_LENGTH, verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [models.UniqueConstraint(
            fields=('name', 'measurement_unit'), name='unique_ingredient')]

    def __str__(self):
        return (
            f'{self.id=:}, '
            f'{self.name=:20}, '
            f'{self.measurement_unit=}')


class Tag(models.Model):
    """Модель для тэгов."""

    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH, unique=True,
        verbose_name='Название тега')
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH, unique=True,
        verbose_name='Слаг')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return (
            f'{self.name=:20}, '
            f'{self.slug=}')


class Recipe(models.Model):
    """Модель для рецептов."""

    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор')
    name = models.TextField(
        'Название рецепта', max_length=RECIPE_TITLE_MAX_LENGTH)
    text = models.TextField('Текст рецепта')
    image = models.ImageField(
        'Изображение', upload_to='recipes/', null=True)
    tags = models.ManyToManyField(
        Tag, verbose_name='Теги публикации')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления в минутах',
        validators=[MinValueValidator(1), MaxValueValidator(1440)])
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientAmount',
        verbose_name='Ингридиенты', related_name='recipes')
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def __str__(self):
        return (
            f'{self.author=:20}, '
            f'{self.title=:20}, '
            f'{self.text=:20}, '
            f'{self.tags=}, '
            f'{self.cooking_time=}, '
            f'{self.slug=}')


class IngredientAmount(models.Model):
    """Связующяя модель для добавления ингридиентов в рецепт."""

    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='Ингридиент')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт',
        related_name='ingredients_amounts', null=True)
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)], verbose_name='Количество')

    class Meta:
        verbose_name = 'Количество ингридиента'
        verbose_name_plural = 'Количество ингридиентов'
        ordering = ('recipe', 'ingredient')
        constraints = [
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique_recipe_ingredient')]

    def __str__(self):
        return (
            f'{self.ingredient=:20}, '
            f'{self.recipe=:20}, '
            f'{self.amount=:20}')


class SelectRecipeBaseModel(models.Model):
    """Модель для добавления рецепта в другую модель."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт')

    class Meta:
        abstract = True
        ordering = ('user',)

    def __str__(self):
        return (
            f'{self.user=:.20}, '
            f'{self.recipe=:.20}')


class Favorite(SelectRecipeBaseModel):
    """Модель для избранного."""

    class Meta(SelectRecipeBaseModel.Meta):
        verbose_name = 'Избранное'
        default_related_name = 'favorite'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='unique_favorite')]


class ShoppingCart(SelectRecipeBaseModel):
    """Модель для корзины."""

    class Meta(SelectRecipeBaseModel.Meta):
        verbose_name = 'Корзина'
        default_related_name = 'customer'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'), name='unique_shopping_cart')]
