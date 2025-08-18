from __future__ import annotations

from typing import Any, Literal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import FavoriteLocation, User
# ----------여기 추가-----------
from couponbook.serializers import PlaceCreateSerializer, PlaceSerializer
from couponbook.models import Place

User: type[AbstractUser] = get_user_model()


class FavoriteLocationSerializer(serializers.ModelSerializer):
    """
    자주 가는 지역(`FavoriteLocation`) 모델을 위한 시리얼라이저입니다.
    사용자의 자주 가는 지역 정보를 직렬화하고 유효성을 검사합니다.
    """
    class Meta:
        model = FavoriteLocation
        fields: list[str] = ["province", "city", "district"]


class BaseRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields: tuple[
            Literal["id"],
            Literal["username"],
            Literal["email"],
            Literal["password"],
            Literal["phone"],
        ] = ("id", "username", "email", "password", "phone")
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
        role: str = self.context["role"]
        password: str = validated_data.pop("password")
        favorite_locations_data = validated_data.pop("favorite_locations", [])
        
        # place_data를 pop하여 변수에 저장합니다.
        place_data = validated_data.pop("place", None)

        user: User = User(**validated_data, role=role)
        user.set_password(password)
        user.save()

        if favorite_locations_data:  # 손님일 경우에만 실행
            for location_data in favorite_locations_data:
                FavoriteLocation.objects.create(user=user, **location_data)

        if place_data:  # 점주일 경우에만 실행
            from couponbook.models import Place
            Place.objects.create(owner=user, **place_data)

        return user


class RegisterCustomerSerializer(BaseRegisterSerializer):
    favorite_locations = FavoriteLocationSerializer(
        many=True, required=True, min_length=1
    )

    class Meta(BaseRegisterSerializer.Meta):
        fields = BaseRegisterSerializer.Meta.fields + ("favorite_locations",)


class RegisterOwnerSerializer(BaseRegisterSerializer):
    # PlaceCreateSerializer를 중첩 시리얼라이저로 추가합니다.
    # required=True로 설정하여 가게 정보가 필수로 등록되도록 합니다.
    place = PlaceCreateSerializer(required=True)

    class Meta(BaseRegisterSerializer.Meta):
        fields = BaseRegisterSerializer.Meta.fields + ("place",)



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
        if favorite_locations_data:
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

    # 점주인 경우 가게 정보를 함께 반환하도록 PlaceSerializer를 추가합니다.
    # -------------여기 추가--------------
    place = serializers.SerializerMethodField()

    def get_place(self, obj: User) -> dict | None:
        """
        사용자가 점주인 경우, 연결된 가게 정보를 반환합니다.
        """
        if not obj.is_owner():
            return None
        try:
            place = obj.place  # 없으면 Place.DoesNotExist 발생
        except place.DoesNotExist:
            return None
        return PlaceSerializer(place).data
    
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "favorite_locations", "place"]
