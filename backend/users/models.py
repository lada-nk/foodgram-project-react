from datetime import date

from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.db import models

from .constants import (
    Role, USERNAME_MAX_LENGTH, PASSWORD_MAX_LENGTH,
    FIRST_NAME_MAX_LENGTH, LAST_NAME_MAX_LENGTH
)


class User(AbstractUser):
    email = models.EmailField(
        'Адресс электронной почты',
        unique=True,
        validators=[EmailValidator(
            message='Введите корректный адрес электронной почты.')
        ],
        error_messages={
            'unique': 'Пользователь с таким адресом'
                      'электронной почты уже существует.',
        },
    )
    username = models.CharField(
        'Имя пользователя',
        unique=True, max_length=USERNAME_MAX_LENGTH,
    )
    first_name = models.CharField(
        'Имя', blank=True, max_length=FIRST_NAME_MAX_LENGTH)
    last_name = models.CharField(
        'Фамилия', blank=True, max_length=LAST_NAME_MAX_LENGTH)
    role = models.CharField(
        'Тип пользователя',
        max_length=max(len(role[0]) for role in Role.choices),
        choices=Role.choices, default=Role.USER
    )
    password = models.CharField(
        'Пароль', max_length=PASSWORD_MAX_LENGTH
        )
    image = models.ImageField(
        upload_to='food/images/',
        null=True,
        default=None
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    @property
    def is_admin(self):
        return self.role == Role.ADMIN or self.is_staff

    def __str__(self):
        return (
            f'{self.username=:.20}, '
            f'{self.email=}, '
            f'{self.role=}, '
            f'{self.first_name=:.20}, '
            f'{self.last_name=:.20}, '
            f'{self.is_staff=}, '
            f'{self.is_active=}, '
        )
