# Generated by Django 3.2.3 on 2024-06-14 15:13

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20240610_1553'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=150, unique=True, validators=[django.core.validators.RegexValidator(code='invalid_username', message='Введите корректное имя пользователя.', regex='[\\w.@+-]+')], verbose_name='Имя пользователя'),
        ),
    ]
