from __future__ import annotations

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema, OpenApiExample

from django.contrib.auth import get_user_model

from .serializers import RegisterSerializer
from .auth import IdentifierTokenObtainPairSerializer

User = get_user_model()


@extend_schema(
    tags=["Auth"],
    summary="손님 회원가입",
    request=RegisterSerializer,
    responses={201: RegisterSerializer},
    examples=[
        OpenApiExample(
            "손님 회원가입 예시",
            value={"username": "alice", "email": "a@ex.com", "password": "P@ssw0rd!", "phone": "01012345678"},
        )
    ],
)
class RegisterCustomerView(APIView):
    """손님(CUSTOMER) 역할 회원 가입 API."""

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data, context={"role": User.Role.CUSTOMER})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(RegisterSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Auth"],
    summary="점주 회원가입",
    request=RegisterSerializer,
    responses={201: RegisterSerializer},
)
class RegisterOwnerView(APIView):
    """점주(OWNER) 역할 회원 가입 API."""

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data, context={"role": User.Role.OWNER})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(RegisterSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Auth"],
    summary="로그인 (username 또는 email + password)",
    examples=[
        OpenApiExample("username 로그인", value={"identifier": "alice", "password": "P@ssw0rd!"}),
        OpenApiExample("email 로그인", value={"identifier": "a@ex.com", "password": "P@ssw0rd!"}),
    ],
)
class LoginView(TokenObtainPairView):
    """JWT 로그인(Access/Refresh 발급)"""

    serializer_class = IdentifierTokenObtainPairSerializer


# Refresh는 기본 뷰 재사용
class RefreshView(TokenRefreshView):
    """JWT 토큰 재발급"""
    pass
