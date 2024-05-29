# Generated by Django 3.2.3 on 2024-05-28 07:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='image',
        ),
        migrations.AddField(
            model_name='user',
            name='avatar',
            field=models.ImageField(default=None, null=True, upload_to='users/'),
        ),
    ]
