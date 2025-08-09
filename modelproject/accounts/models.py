from __future__ import annotations

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    커스텀 사용자 모델.
    기본 AbstractUser(username, password, email 등)에 role, phone을 확장합니다.
    """

    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "손님"
        OWNER = "OWNER", "점주"

    role: str = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        help_text="사용자 역할",
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
