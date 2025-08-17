from typing import Literal

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("권한", {"fields": ("role",)}),
    )

    list_display: tuple[Literal['username'], Literal['email'], Literal['role'], Literal['is_staff']] = (
        "username",
        "email",
        "role",
        "is_staff",
    )