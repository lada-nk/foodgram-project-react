from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator, RegexValidator
from django.db import models
from django.db.models import Q, F

from .constants import (
    FIRST_NAME_MAX_LENGTH, LAST_NAME_MAX_LENGTH,
    PASSWORD_MAX_LENGTH, USERNAME_MAX_LENGTH)


class User(AbstractUser):
    """Модель для пользлвателя."""

    email = models.EmailField(
        'Адресс электронной почты',
        unique=True,
        validators=[EmailValidator(
            message='Введите корректный адрес электронной почты.')],
        error_messages={
            'unique': 'Пользователь с таким адресом'
                      'электронной почты уже существует.'})
    username = models.CharField(
        'Имя пользователя',
        unique=True, max_length=USERNAME_MAX_LENGTH,
        validators=[
            RegexValidator(
                regex=r'[\w.@+-]+',
                message='Введите корректное имя пользователя.',
                code='invalid_username')])
    first_name = models.CharField(
        'Имя', blank=True, max_length=FIRST_NAME_MAX_LENGTH)
    last_name = models.CharField(
        'Фамилия', blank=True, max_length=LAST_NAME_MAX_LENGTH)
    password = models.CharField(
        'Пароль', max_length=PASSWORD_MAX_LENGTH)
    avatar = models.ImageField(
        'Аватар', upload_to='users/', null=True, default=None)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return (
            f'{self.username=}, '
            f'{self.email=}, '
            f'{self.first_name=}, '
            f'{self.last_name=}, '
            f'{self.is_staff=}, '
            f'{self.is_active=}')


class Follow(models.Model):
    """Модель для подписок."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='follower', verbose_name='Кто подписан')
    following = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='following', verbose_name='На кого подписан')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user',)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'following'), name='unique_subscription'),
            models.CheckConstraint(
                check=~Q(following=F('user')), name='not_self_folowing'))

    def __str__(self):
        return (
            f'{self.user=}, '
            f'{self.following=}')
