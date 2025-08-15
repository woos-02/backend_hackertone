from __future__ import annotations

from typing import Any, Literal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

User: type[AbstractUser] = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    손님/점주 공용 회원가입 시리얼라이저.
    role은 뷰에서 강제 세팅합니다(엔드포인트 분리 요구사항 반영).
    """

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields: tuple[Literal['id'], Literal['username'], Literal['email'], Literal['password'], Literal['phone']] = ("id", "username", "email", "password", "phone")
        extra_kwargs: dict[str, dict[str, bool]] = {
            "email": {"required": True},
        }

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> User:
        role: str = self.context["role"]  # 뷰에서 주입
        password: str = validated_data.pop("password")
        user: User = User(**validated_data, role=role)
        user.set_password(password)
        user.save()
        return user


class UserMiniSerializer(serializers.ModelSerializer):
    """토큰 응답에 실어보낼 최소 사용자 정보."""

    class Meta:
        model = User
        fields: tuple[Literal['id'], Literal['username'], Literal['role']] = ("id", "username", "role")
