from typing import Literal

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, FavoriteLocation


class FavoriteLocationInline(admin.TabularInline):
    """
    User 모델 편집 페이지에 FavoriteLocation을 인라인으로 보여주기 위한 클래스.
    """
    model = FavoriteLocation
    extra = 1  # 기본적으로 추가할 수 있는 빈 필드 수
    fields = ['province', 'city', 'district']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    사용자 모델을 Django 관리자 페이지에 등록하고,
    표시 필드와 필드셋을 커스터마이즈하는 클래스입니다.
    """
    fieldsets = BaseUserAdmin.fieldsets + (
        ("권한", {"fields": ("role",)}),
    )

    list_display: tuple[Literal['username'], Literal['email'], Literal['role'], Literal['is_staff'], Literal['get_favorite_locations']] = (
        "username",
        "email",
        "role",
        "is_staff",
        "get_favorite_locations",
    )
    
    # FavoriteLocationInline을 인라인으로 추가
    inlines = [FavoriteLocationInline]

    # 목록 페이지에 '자주 가는 지역'을 표시하는 사용자 정의 메서드
    @admin.display(description="자주 가는 지역")
    def get_favorite_locations(self, obj: User) -> str:
        """
        사용자의 모든 자주 가는 지역을 콤마로 구분된 문자열로 반환합니다.
        """
        locations = obj.favorite_locations.all()
        location_names = [f"{loc.province} {loc.city} {loc.district}" for loc in locations]
        return ", ".join(location_names) or "없음"



@admin.register(FavoriteLocation)
class FavoriteLocationAdmin(admin.ModelAdmin):
    """
    FavoriteLocation 모델을 관리자 페이지에 등록합니다.
    """
    list_display = ['user', 'province', 'city', 'district']
    search_fields = ['user__username', 'province', 'city', 'district']
    list_filter = ['province', 'city']