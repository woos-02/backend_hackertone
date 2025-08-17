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
    class Meta:
        model = FavoriteLocation
        fields = ["province", "city", "district"]


class RegisterSerializer(serializers.ModelSerializer):
    """
    손님/점주 공용 회원가입 시리얼라이저.
    role은 뷰에서 강제 세팅합니다(엔드포인트 분리 요구사항 반영).
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
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> User:
        role: str = self.context["role"]  # 뷰에서 주입
        password: str = validated_data.pop("password")

        favorite_locations_data = validated_data.pop("favorite_locations", [])

        user: User = User(**validated_data, role=role)
        user.set_password(password)
        user.save()

        for location_data in favorite_locations_data:
            FavoriteLocation.objects.create(user=user, **location_data)

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    사용자 프로필 업데이트 시리얼라이저.
    """

    favorite_locations = FavoriteLocationSerializer(many=True, required=False)

    class Meta:
        model = User
        fields = ["username", "email", "phone", "favorite_locations"]
        extra_kwargs = {"email": {"required": False}, "username": {"required": False}}

    @transaction.atomic
    def update(self, instance, validated_data):
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
    """토큰 응답에 실어보낼 최소 사용자 정보."""

    class Meta:
        model = User
        fields: tuple[Literal["id"], Literal["username"], Literal["role"]] = (
            "id",
            "username",
            "role",
        )


class MeSerializer(serializers.ModelSerializer):
    """
    MeView를 위한 시리얼라이저.
    사용자의 기본 정보와 favorite_locations를 포함합니다.
    """

    favorite_locations = FavoriteLocationSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "favorite_locations"]
