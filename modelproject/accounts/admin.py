from typing import Literal

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    사용자 모델을 Django 관리자 페이지에 등록하고,
    표시 필드와 필드셋을 커스터마이즈하는 클래스입니다.

    기본 UserAdmin을 상속받아 role(권한)과 favorite(선호 지역) 필드를
    추가하여 관리자 페이지에서 쉽게 볼 수 있도록 합니다.
    """
    fieldsets = BaseUserAdmin.fieldsets + (
        ("권한", {"fields": ("role",)}),
        ("Favorite", {"fields": ("favorite_province", "favorite_city", "favorite_district")}),
    )

    list_display: tuple[Literal['username'], Literal['email'], Literal['role'], Literal['is_staff'], Literal['favorite_province'], Literal['favorite_city'], Literal['favorite_district']] = (
        "username",
        "email",
        "role",
        "is_staff",
        "favorite_province",
        "favorite_city",
        "favorite_district",
    )