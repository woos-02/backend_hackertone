from __future__ import annotations

from typing import Any

from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class IdentifierTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    username 또는 email을 identifier로 받아 인증합니다.
    """

    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        identifier: str = attrs.get("identifier", "")
        password: str = attrs.get("password", "")

        # identifier가 username or email 어느 쪽이든 검색
        try:
            user = User.objects.get(Q(username=identifier) | Q(email=identifier))
            username = user.username
        except User.DoesNotExist:
            # username으로 그냥 진행해 보고 실패 유도
            username = identifier

        # DRF의 authenticate로 검증
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError({"detail": "잘못된 자격 증명입니다."})

        # parent가 기대하는 'username' 키로 세팅
        data = {"username": user.username, "password": password}
        token_data = super().validate(data)

        # 유저 최소 정보 동봉
        token_data["user"] = {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        }
        return token_data
