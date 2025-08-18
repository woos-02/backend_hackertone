from __future__ import annotations

from typing import Any, Literal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import FavoriteLocation, User

User: type[AbstractUser] = get_user_model()


class FavoriteLocationSerializer(serializers.ModelSerializer):
    """
    자주 가는 지역(`FavoriteLocation`) 모델을 위한 시리얼라이저입니다.
    사용자의 자주 가는 지역 정보를 직렬화하고 유효성을 검사합니다.
    """
    class Meta:
        model = FavoriteLocation
        fields: list[str] = ["province", "city", "district"]


class RegisterSerializer(serializers.ModelSerializer):
    """
    손님 또는 점주 회원가입을 위한 공용 시리얼라이저입니다.

    **특징:**
    - `password` 필드는 쓰기 전용(`write_only`)이며, 비밀번호 유효성 검사를 수행합니다.
    - `favorite_locations` 필드는 `FavoriteLocationSerializer`를 사용하여 중첩 직렬화를 지원합니다.
    - `favorite_locations`는 **최소 1개 이상 필수**입니다.
    - `role`은 API 뷰(`views.py`)에서 결정되어 시리얼라이저 컨텍스트로 전달됩니다.
    """
    password = serializers.CharField(write_only=True, min_length=8)

    favorite_locations = FavoriteLocationSerializer(
        many=True, required=True, min_length=1
    )

    class Meta:
        model = User
        fields: tuple[
            Literal["id"],
            Literal["username"],
            Literal["email"],
            Literal["password"],
            Literal["phone"],
            Literal["favorite_locations"],
        ] = ("id", "username", "email", "password", "phone", "favorite_locations")
        extra_kwargs: dict[str, dict[str, bool]] = {
            "email": {"required": True},
        }

    def validate_password(self, value: str) -> str:
        """Django의 기본 비밀번호 유효성 검사 규칙을 적용합니다."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> User:
        """
        새로운 사용자(`User`)와 관련된 자주 가는 지역(`FavoriteLocation`) 객체를 함께 생성합니다.
        `role` 값은 뷰에서 전달된 컨텍스트를 사용합니다.
        """
        role: str = self.context["role"]  # 뷰에서 주입
        password: str = validated_data.pop("password")

        # favorite_locations 데이터를 별도로 분리합니다.
        favorite_locations_data = validated_data.pop("favorite_locations", [])

        # User 객체 생성 및 비밀번호 설정
        user: User = User(**validated_data, role=role)
        user.set_password(password)
        user.save()

        # 분리한 favorite_locations 데이터를 사용해 FavoriteLocation 객체들을 생성합니다.
        for location_data in favorite_locations_data:
            FavoriteLocation.objects.create(user=user, **location_data)

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    사용자 프로필 업데이트를 위한 시리얼라이저입니다.
    `username`, `email`, `phone`, `favorite_locations` 필드를 수정할 수 있습니다.

    **특징:**
    - `email`과 `username`은 업데이트 시 필수가 아닙니다.
    - `favorite_locations`를 업데이트하면 기존 데이터는 모두 삭제되고 새로운 데이터로 대체됩니다.
    """

    favorite_locations = FavoriteLocationSerializer(many=True, required=False)

    class Meta:
        model = User
        fields: list[str] = ["username", "email", "phone", "favorite_locations"]
        extra_kwargs: dict[str, dict[str, bool]] = {"email": {"required": False}, "username": {"required": False}}

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        사용자 프로필과 즐겨찾는 지역 데이터를 업데이트합니다.

        **로직:**
        1. 요청 데이터에서 `favorite_locations`를 분리합니다.
        2. `User` 모델 필드(`username`, `email`, `phone`)를 업데이트합니다.
        3. 기존의 모든 `FavoriteLocation` 데이터를 삭제합니다.
        4. 새로운 `FavoriteLocation` 데이터로 객체들을 다시 생성합니다.
        """
        # favorite_locations 데이터 분리
        favorite_locations_data = validated_data.pop("favorite_locations", [])

        # User 모델 업데이트
        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)
        instance.phone = validated_data.get("phone", instance.phone)
        instance.save()

        # 기존 favorite_locations 데이터 모두 삭제 후,
        # 새로운 데이터로 다시 생성
        instance.favorite_locations.all().delete()
        for location_data in favorite_locations_data:
            FavoriteLocation.objects.create(user=instance, **location_data)

        return instance


class UserMiniSerializer(serializers.ModelSerializer):
    """
    JWT 토큰 응답에 포함될 최소한의 사용자 정보 시리얼라이저입니다.
    """

    class Meta:
        model = User
        fields: tuple[Literal["id"], Literal["username"], Literal["role"]] = (
            "id",
            "username",
            "role",
        )


class MeSerializer(serializers.ModelSerializer):
    """
    `MeView` (내 프로필 조회)를 위한 시리얼라이저입니다.
    사용자의 기본 정보(`id`, `username`, `email`, `role`)와
    연결된 자주 가는 지역(`favorite_locations`) 정보를 함께 반환합니다.
    """

    favorite_locations = FavoriteLocationSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "favorite_locations"]
