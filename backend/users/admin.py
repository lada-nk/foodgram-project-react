from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Follow, User

UserAdmin.fieldsets += (
    ('Extra Fields', {'fields': ('avatar',)}),
)
admin.site.register(User, UserAdmin)
admin.site.register(Follow)
