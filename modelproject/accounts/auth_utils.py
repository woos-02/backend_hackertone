# from __future__ import annotations

# from typing import Any

# from django.contrib.auth import authenticate, get_user_model
# from django.contrib.auth.models import AbstractUser
# from django.db.models import Q
# from rest_framework import serializers
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# User: type[AbstractUser] = get_user_model()


# class IdentifierTokenObtainPairSerializer(TokenObtainPairSerializer):
#     """
#     username 또는 email을 identifier로 받아 인증합니다.
#     """

#     identifier = serializers.CharField()
#     password = serializers.CharField(write_only=True)

#     def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
#         identifier: str = attrs.get("identifier", "")
#         password: str = attrs.get("password", "")

#         # identifier가 username or email 어느 쪽이든 검색
#         try:
#             user = User.objects.get(Q(username=identifier) | Q(email=identifier))
#             username = user.username
#         except User.DoesNotExist:
#             # username으로 그냥 진행해 보고 실패 유도
#             username = identifier

#         # DRF의 authenticate로 검증
#         user = authenticate(username=username, password=password)
#         if not user:
#             raise serializers.ValidationError({"detail": "잘못된 자격 증명입니다."})

#         # parent가 기대하는 'username' 키로 세팅
#         data = {"username": user.username, "password": password}
#         token_data = super().validate(data)

#         # 유저 최소 정보 동봉
#         token_data["user"] = {
#             "id": user.id,
#             "username": user.username,
#             "role": user.role,
#         }
#         return token_data

# accounts/auth_utils.py
from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class IdentifierTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    username 또는 email(=identifier) + password 로 로그인.
    username/identifier 중 하나만 보내면 됩니다.
    """

    identifier = serializers.CharField(write_only=True, required=False)  # 선택

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 부모가 동적으로 추가한 username 필드를 선택으로 변경
        if self.username_field in self.fields:
            self.fields[self.username_field].required = False

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        identifier = attrs.pop("identifier", None)
        username = attrs.get(self.username_field)

        if not username and not identifier:
            raise serializers.ValidationError(
                {"identifier": ["username 또는 email 중 하나를 보내주세요."]}
            )

        if not username and identifier:
            try:
                u = User.objects.get(
                    Q(username__iexact=identifier) | Q(email__iexact=identifier)
                )
                attrs[self.username_field] = getattr(u, self.username_field)
            except User.DoesNotExist:
                # 없는 값이면 그대로 시도 → 부모 validate에서 인증 실패 처리
                attrs[self.username_field] = identifier

        return super().validate(attrs)
