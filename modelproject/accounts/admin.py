from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# 커스텀 User 모델을 Django 관리자 페이지에 등록
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # 필요한 경우 여기에 사용자 관리 설정을 추가할 수 있습니다.
    pass