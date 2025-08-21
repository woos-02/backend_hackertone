from __future__ import annotations

from typing import Any, Literal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers
# 점주 가입 시 가게 정보(Place 모델)를 중첩으로 생성/조회하기 위해 참조
from couponbook.serializers import PlaceCreateSerializer, PlaceSerializer
from couponbook.models import Place
from .models import FavoriteLocation, User


User: type[AbstractUser] = get_user_model()

# ------------------------ 자주 가는 지역 -------------------------
class FavoriteLocationSerializer(serializers.ModelSerializer):
    """
    자주 가는 지역(`FavoriteLocation`) 모델을 위한, 정보를 직렬화하는 시리얼라이저입니다.
    회원가입 및 프로필 수정 시 사용됩니다.
    """
    class Meta:
        model = FavoriteLocation
        fields: list[str] = ["province", "city", "district"]
        # 예시 데이터:
        # {
        #     "province": "경기도",
        #     "city": "수원시",
        #     "district": "장안구"
        # }

# ------------------------ 회원가입 기반 로직 -------------------------
class BaseRegisterSerializer(serializers.ModelSerializer):
    """
    사용자 회원 가입의 기본 필드를 정의하는 시리얼라이저입니다.
    손님(Customer) 및 점주(Owner) 회원 가입 시리얼라이저의 기반이 됩니다.
    """
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
        """
        Django의 기본 비밀번호 유효성 검사 규칙을 적용합니다.
        (예: 최소 길이, 일반적인 비밀번호 사용 여부 등)
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> User:
        """
        새로운 사용자를 생성하고, 역할(role)에 따라 추가 정보를 처리합니다.

        - 'role'이 'customer'인 경우: 'favorite_locations'를 생성합니다.
        - 'role'이 'owner'인 경우: 'place'를 생성합니다.
        """
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

# ------------------------ 손님 회원가입 -------------------------
class RegisterCustomerSerializer(BaseRegisterSerializer):
    """
    '손님' 회원의 가입을 처리하는 시리얼라이저입니다.
    BaseRegisterSerializer를 상속하며, '자주 가는 지역' 필드를 추가합니다.

    - 필수 필드: 'favorite_locations' (최소 1개 이상의 지역 정보)
    """
    favorite_locations = FavoriteLocationSerializer(
        many=True, required=True, min_length=1
    )

    class Meta(BaseRegisterSerializer.Meta):
        fields: tuple[Literal['id'], Literal['username'], Literal['email'], Literal['password'], Literal['phone']] = BaseRegisterSerializer.Meta.fields + ("favorite_locations",)

# ------------------------ 점주 회원가입 -------------------------
class RegisterOwnerSerializer(BaseRegisterSerializer):
    """
    '점주' 회원의 가입을 처리하는 시리얼라이저입니다.
    BaseRegisterSerializer를 상속하며, '가게' 정보 필드를 추가합니다.

    - 필수 필드: 'place' (가게 생성 정보)
    """
    # place = PlaceCreateSerializer(required=True)

    class Meta(BaseRegisterSerializer.Meta):
        fields: tuple[Literal['id'], Literal['username'], Literal['email'], Literal['password'], Literal['phone']] = BaseRegisterSerializer.Meta.fields + ("place",)


# ------------------------ 사용자 프로필 업데이트 -------------------------
class UserUpdateSerializer(serializers.ModelSerializer):
    """
    사용자 프로필 업데이트를 위한 시리얼라이저입니다.
    `username`, `email`, `phone`, `favorite_locations` 필드를 수정할 수 있습니다.

    **특징:**
    - 모든 필드는 업데이트 시 필수가 아닙니다.
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
        사용자 프로필과 '자주 가는 지역' 데이터를 업데이트합니다.

        **로직:**
        1. 요청 데이터에서 `favorite_locations`를 분리합니다.
        2. `User` 모델 필드(`username`, `email`, `phone`)를 업데이트합니다.
        3 'favorite_locations' 데이터가 있는 경우: 기존 데이터를 모두 삭제하고, 새로운 데이터로 재등록합니다.
        -> 기존의 모든 `FavoriteLocation` 데이터를 삭제합니다.
        -> 새로운 `FavoriteLocation` 데이터로 객체들을 다시 생성합니다.
        """
        # favorite_locations 데이터 분리
        favorite_locations_data = validated_data.pop("favorite_locations", [])

        # User 모델 업데이트
        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)
        instance.phone = validated_data.get("phone", instance.phone)
        instance.save()

        # 'favorite_locations'가 요청에 포함된 경우에만 업데이트 로직 실행
        if favorite_locations_data:
            instance.favorite_locations.all().delete()
            for location_data in favorite_locations_data:
                FavoriteLocation.objects.create(user=instance, **location_data)

        return instance

# ------------------------ 사용자 기본 정보 반환 -------------------------
class UserMiniSerializer(serializers.ModelSerializer):
    """
    JWT 토큰 응답에 포함될 최소한의 사용자 정보를 직렬화하는 시리얼라이저입니다.
    로그인 성공 시 반환되는 데이터 구조를 정의합니다.

    - 출력 필드: 'id', 'username', 'role'
    """

    class Meta:
        model = User
        fields: tuple[Literal["id"], Literal["username"], Literal["role"]] = (
            "id",
            "username",
            "role",
        )

# ------------------------ 사용자 프로필 조회 -------------------------
class MeSerializer(serializers.ModelSerializer):
    """
    로그인한 사용자의 상세 프로필 정보를 조회하기 위한 시리얼라이저입니다.
    `MeView` (내 프로필 조회) API에 사용됩니다.

    - 출력 필드: 'id', 'username', 'email', 'role'
    - 추가 필드: 'favorite_locations' (손님인 경우), 'place' (점주인 경우)
    """

    favorite_locations = FavoriteLocationSerializer(many=True, read_only=True)

    place = serializers.SerializerMethodField()

    def get_place(self, obj: User) -> dict | None:
        """
        사용자가 점주인 경우, 연결된 가게 정보를 반환합니다.
        가게 정보가 없는 경우 'None'을 반환합니다.
        """
        if not obj.is_owner():
            return None
        try:
            place = obj.place  # 없으면 Place.DoesNotExist 발생
        except Place.DoesNotExist:
            return None
        return PlaceSerializer(place).data
    
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "favorite_locations", "place"]
