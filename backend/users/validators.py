import re

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model


def forbidden_usernames(value: str):
    """Валидатор username."""
    forbidden_symbols = re.sub(r'[\w.@+-]+', '', value)
    if forbidden_symbols:
        raise ValidationError(
            f'Нельзя использовать {"".join(set(forbidden_symbols))} '
            f'в username'
        )
    return value
