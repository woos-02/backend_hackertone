from __future__ import annotations

from typing import Literal

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

# ------------------------ User -------------------------
class User(AbstractUser):
    """
    커스텀 사용자 모델.
    기본 AbstractUser(username, password, email 등)에 role, phone을 확장합니다.
    """

    class Role(models.TextChoices):
        """
        사용자의 역할을 정의하는 클래스입니다.
        'CUSTOMER: 손님'와 'OWNER: 점주' 두 가지 역할을 제공합니다.
        'models.CharField'의 'choices' 옵션과 함께 사용되어,
        데이터베이스에 저장될 값과 사용자에게 보여줄 값을 구분합니다.
        """

        CUSTOMER: tuple[Literal["CUSTOMER"], Literal["손님"]] = "CUSTOMER", "손님"
        OWNER: tuple[Literal["OWNER"], Literal["점주"]] = "OWNER", "점주"

    role: str = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        help_text="사용자 역할(CUSTOMER/OWNER)",
    )
    phone: str | None = models.CharField(
        max_length=20, null=True, blank=True, help_text="연락처(선택)"
    )

    def is_owner(self) -> bool:
        """점주 여부 헬퍼."""
        return self.role == self.Role.OWNER

    def is_customer(self) -> bool:
        """손님 여부 헬퍼."""
        return self.role == self.Role.CUSTOMER

# ------------------------ 자주 가는 지역 -------------------------
class FavoriteLocation(models.Model):
    """
    사용자가 자주 가는 지역을 저장하는 모델.
    한 명의 사용자는 여러 개의 FavoriteLocation을 가질 수 있습니다.
    """

    user: models.ForeignKey[User] = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favorite_locations"
    )
    province: models.CharField[str] = models.CharField(max_length=50)  # 시/도
    city: models.CharField[str] = models.CharField(max_length=50)  # 시/군/구
    district: models.CharField[str] = models.CharField(max_length=50)  # 읍/면/동

    class Meta:
        # 한 사용자가 같은 지역을 중복해서 저장하지 못하도록 설정
        unique_together: tuple[Literal['user'], Literal['province'], Literal['city'], Literal['district']] = ("user", "province", "city", "district")
        verbose_name = "자주 가는 지역"
        verbose_name_plural = "자주 가는 지역들"

    def __str__(self) -> str:
        return f"{self.user.username} - {self.province} {self.city} {self.district}"
