from __future__ import annotations

from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .auth_utils import IdentifierTokenObtainPairSerializer
from .serializers import RegisterSerializer

User = get_user_model()


@extend_schema(
    tags=["Auth"],
    summary="손님 회원가입",
    request=RegisterSerializer,
    responses={201: RegisterSerializer},
    examples=[
        OpenApiExample(
            "손님 회원가입 예시",
            value={
                "username": "alice",
                "email": "a@ex.com",
                "password": "P@ssw0rd!",
                "phone": "01012345678",
            },
        )
    ],
)
class RegisterCustomerView(APIView):
    """손님(CUSTOMER) 역할 회원 가입 API.

    Body(JSON 또는 x-www-form-urlencoded)
      - username: str
      - email: str
      - password: str
      - phone: str
    """

    # DRF 브라우저에서 JSON/폼 모두 받을 수 있도록 파서 명시
    parser_classes = (JSONParser, FormParser, MultiPartParser)

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(
            data=request.data, context={"role": User.Role.CUSTOMER}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 비밀번호는 write_only 이므로 응답에 포함되지 않음
        return Response(RegisterSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Auth"],
    summary="점주 회원가입",
    request=RegisterSerializer,
    responses={201: RegisterSerializer},
    # 점주 회원가입 예시 -> Customer와 동일
)
class RegisterOwnerView(APIView):
    """
    점주(OWNER) 역할 회원 가입 API.
    """

    parser_classes: tuple[type[JSONParser], type[FormParser], type[MultiPartParser]] = (
        JSONParser,
        FormParser,
        MultiPartParser,
    )

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(
            data=request.data, context={"role": User.Role.OWNER}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(RegisterSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Auth"],
    summary="로그인 (username 또는 email + password)",
    description=(
        "identifier 에는 **username 또는 email** 중 하나를 넣습니다. "
        "혹은 username/password 쌍을 그대로 보내도 됩니다."
    ),
    examples=[
        OpenApiExample(
            "identifier=username",
            value={"identifier": "alice", "password": "P@ssw0rd!"},
        ),
        OpenApiExample(
            "identifier=email",
            value={"identifier": "a@ex.com", "password": "P@ssw0rd!"},
        ),
        OpenApiExample(
            "username 직접", value={"username": "alice", "password": "P@ssw0rd!"}
        ),
    ],
)
class LoginView(TokenObtainPairView):
    """
    JWT 로그인(Access/Refresh 발급)

    Body(JSON)
      - identifier: str (username 또는 email) # 선택
      - username: str # 선택
      - password: str # 필수

    identifier 또는 username 중 하나만 보내면 됩니다.
    """

    serializer_class = IdentifierTokenObtainPairSerializer


# Refresh는 기본 뷰 재사용
class RefreshView(TokenRefreshView):
    """JWT 토큰 재발급(Refresh -> Access)"""

    pass


@extend_schema(
    tags=["Auth"],
    summary="내 프로필 조회 (JWT 보호)",
    description="Authorization: Bearer <access_token> 헤더가 필요합니다.",
    responses={
        200: OpenApiExample(
            "성공 예시",
            value={
                "id": 1,
                "username": "alice",
                "email": "a@ex.com",
                "role": "CUSTOMER",
            },
        ),
        401: OpenApiExample(
            "인증 실패",
            value={"detail": "Authentication credentials were not provided."},
        ),
    },
)
class MeView(APIView):
    """
    인증된 사용자의 최소 프로필을 반환하는 보호 엔드포인트.
    프론트에서 로그인 직후 사용자 정보를 가져올 때 활용하세요.
    """

    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user: User = request.user  # type: ignore[assignment]
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": getattr(user, "email", None),
                "role": getattr(user, "role", None),
            },
            status=status.HTTP_200_OK,
        )
