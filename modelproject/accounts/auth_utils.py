from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # 부모가 동적으로 추가한 username 필드를 선택으로 변경
        if self.username_field in self.fields:
            self.fields[self.username_field].required = False

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """
    사용자로부터 'identifier' 또는 'username'을 받아 유효성을 검사합니다.

    'identifier' 필드는 username이나 email 중 하나를 담을 수 있습니다.
    만약 username과 identifier 둘 다 없으면 에러를 발생시킵니다.
    identifier만 있을 경우, username 또는 email과 일치하는 사용자를 찾아
    'TokenObtainPairSerializer'의 'username' 필드에 실제 username을 할당합니다.
    """
        identifier = attrs.pop("identifier", None)
        username: Any | None = attrs.get(self.username_field)

        if not username and not identifier:
            raise serializers.ValidationError(
                {"identifier": ["username 또는 email 중 하나를 보내주세요."]}
            )

        if not username and identifier:
            try:
                u: AbstractUser = User.objects.get(
                    Q(username__iexact=identifier) | Q(email__iexact=identifier)
                )
                attrs[self.username_field] = getattr(u, self.username_field)
            except User.DoesNotExist:
                # 없는 값이면 그대로 시도 → 부모 validate에서 인증 실패 처리
                attrs[self.username_field] = identifier

        return super().validate(attrs)
