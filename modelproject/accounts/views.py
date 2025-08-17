from __future__ import annotations

from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics, permissions, status  # 여기 추가
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .auth_utils import IdentifierTokenObtainPairSerializer
from .models import FavoriteLocation
from .serializers import (
    RegisterSerializer,
    MeSerializer,
    UserMiniSerializer,
    UserUpdateSerializer,
)

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
                "favorite_locations": [
                    {"province": "경기도", "city": "성남시", "district": "분당구"}
                ],
            },
        )
    ],
)
class RegisterCustomerView(APIView):
    """
    손님(CUSTOMER) 역할로 회원 가입을 처리하는 API 뷰입니다.

    POST 요청을 통해 사용자 이름, 이메일, 비밀번호, 연락처,
    그리고 **최소 1개 이상의 즐겨찾는 지역** 정보를 받아
    새로운 '손님' 사용자를 생성합니다.

    Body(JSON 또는 x-www-form-urlencoded)
      - username: str
      - email: str
      - password: str
      - phone: str
      - favorite_locations: str
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

    손님 회원가입과 동일한 방식으로 작동하지만, 사용자 역할만 '점주'로 설정됩니다.
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

    identifier 또는 username 중 하나만 보내면 됩니다. 이후 access/refresh 토큰 쌍을 발급합니다.
    """

    serializer_class = IdentifierTokenObtainPairSerializer


# Refresh는 기본 뷰 재사용
class RefreshView(TokenRefreshView):
    """JWT 토큰 재발급(Refresh -> Access) 뷰입니다."""

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
                "favorite_locations": [
                    {"province": "경기도", "city": "성남시", "district": "분당구"}
                ],
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
        serializer = MeSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    마이페이지 프로필 조회 및 수정 뷰.
    GET: 사용자 프로필 정보 조회
    PUT/PATCH: 사용자 프로필 정보 수정
    """

    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # 현재 로그인된 사용자 객체를 반환합니다.
        return self.request.user

    # --- 추가된 부분 ---


class LogoutView(APIView):
    """
    로그아웃 API. Refresh 토큰을 블랙리스트에 추가하여 무효화합니다.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="로그아웃",
        request={
            "application/json": {
                "example": {"refresh_token": "your_refresh_token_here"}
            }
        },
        responses={
            200: {"description": "로그아웃 성공"},
            400: {"description": "유효하지 않은 토큰"},
        },
    )
    def post(self, request: Request) -> Response:
        try:
            refresh_token = request.data["refresh_token"]
            # RefreshToken 생성 시 유효하지 않은 토큰이면 여기서 TokenError 예외 발생
            token = RefreshToken(refresh_token)
            
            # OutstandingToken 테이블에서 토큰을 가져옵니다.
            outstanding_token = OutstandingToken.objects.filter(token=token).first()

            # 토큰이 존재하면 BlacklistedToken에 추가합니다.
            if outstanding_token:
                BlacklistedToken.objects.create(token=outstanding_token)
            
            return Response(
                {"detail": "Successfully logged out."}, status=status.HTTP_200_OK
            )

        except TokenError as e:
            # TokenError가 발생하면 유효하지 않은 토큰으로 간주하고 Bad Request 응답을 보냅니다.
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            # 'refresh_token' 필드가 없는 경우 KeyError 발생
            return Response(
                {"error": "refresh_token field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # 그 외의 모든 예외 처리
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
