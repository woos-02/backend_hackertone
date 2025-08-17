from __future__ import annotations

from typing import Literal

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    커스텀 사용자 모델.
    기본 AbstractUser(username, password, email 등)에 role, phone을 확장합니다.
    """

    class Role(models.TextChoices):
        """
    사용자의 역할을 정의하는 클래스입니다.
    'CUSTOMER'와 'OWNER' 두 가지 역할을 제공합니다.
    'models.CharField'의 'choices' 옵션과 함께 사용되어,
    데이터베이스에 저장될 값과 사용자에게 보여줄 값을 구분합니다.
    """
        CUSTOMER: tuple[Literal["CUSTOMER"], Literal["손님"]] = "CUSTOMER", "손님"
        OWNER: tuple[Literal["OWNER"], Literal["점주"]] = "OWNER", "점주"

    role: str = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        help_text="사용자 역할",
    )
    phone: str | None = models.CharField(
        max_length=20, null=True, blank=True, help_text="연락처(선택)"
    )
    
    favorite_province: models.CharField[str] = models.CharField(max_length=50, blank=True, help_text="자주 가는 시/도")
    favorite_city: models.CharField[str] = models.CharField(max_length=50, blank=True, help_text="자주 가는 시/군/구")
    favorite_district: models.CharField[str] = models.CharField(max_length=50, blank=True, help_text="자주 가는 읍/면/동")

    def is_owner(self) -> bool:
        """점주 여부 헬퍼."""
        return self.role == self.Role.OWNER

    def is_customer(self) -> bool:
        """손님 여부 헬퍼."""
        return self.role == self.Role.CUSTOMER
