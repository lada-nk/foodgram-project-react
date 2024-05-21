from django.db import models


class Role(models.TextChoices):
    """Пользовательские роли."""

    USER = 'user', 'user'
    ADMIN = 'admin', 'admin'


EMAIL_MAX_LENGTH = 254
USERNAME_MAX_LENGTH = 150
FIRST_NAME_MAX_LENGTH = 150
LAST_NAME_MAX_LENGTH = 150
PASSWORD_MAX_LENGTH = 150
