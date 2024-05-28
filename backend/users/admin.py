from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Follow

UserAdmin.fieldsets += (
    ('Extra Fields', {'fields': ('role',)}),
)
admin.site.register(User, UserAdmin)
admin.site.register(Follow)
