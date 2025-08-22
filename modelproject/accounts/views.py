from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, AnonymousUser
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .auth_utils import IdentifierTokenObtainPairSerializer
from .serializers import (
    MeSerializer,
    RegisterCustomerSerializer,
    RegisterOwnerSerializer,
    UserMiniSerializer,
    UserUpdateSerializer,
)

User: type[AbstractUser] = get_user_model()


# ------------------------ 손님 회원가입 -------------------------
@extend_schema(
    tags=["Auth"],
    summary="손님 회원가입",
    description="""
    새로운 **손님(CUSTOMER)** 사용자를 생성하는 엔드포인트입니다.
    `username`, `email`, `password`, `phone` 및 **최소 1개 이상의 `favorite_locations`(자주 가는 지역)** 정보를 요청 본문에 담아 보냅니다.
    """,
    request=RegisterCustomerSerializer,
    responses={201: RegisterCustomerSerializer},
    auth=None,
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
    그리고 **최소 1개 이상의 자주 가는 지역** 정보를 받아
    새로운 '손님' 사용자를 생성합니다.
    """

    # DRF 브라우저에서 JSON/폼 모두 받을 수 있도록 파서 명시
    parser_classes: tuple[type[JSONParser], type[FormParser], type[MultiPartParser]] = (
        JSONParser,
        FormParser,
        MultiPartParser,
    )
    authentication_classes: tuple = ()

    def post(self, request: Request) -> Response:
        """
        새로운 손님 사용자를 생성합니다.
        `RegisterCustomerSerializer`를 사용해 요청 데이터를 검증하고, `CUSTOMER` 역할을 할당합니다.
        """
        serializer = RegisterCustomerSerializer(
            data=request.data, context={"role": User.Role.CUSTOMER}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 비밀번호는 write_only 이므로 응답에 포함되지 않음
        return Response(
            RegisterCustomerSerializer(user).data, status=status.HTTP_201_CREATED
        )


# ------------------------ 점주 회원가입 -------------------------
@extend_schema(
    tags=["Auth"],
    summary="점주 회원가입",
    description="""
    새로운 **점주(OWNER)** 사용자를 생성하는 엔드포인트입니다.
    `username`, `email`, `password`, `phone` 및 **가게 정보**를 요청 본문에 담아 보냅니다.
    """,
    request=RegisterOwnerSerializer,
    responses={201: RegisterOwnerSerializer},
    auth=None,
    # 점주 회원가입 예시 -> Customer와 동일
)
class RegisterOwnerView(APIView):
    """
    점주(OWNER) 역할로 회원가입을 처리하는 API 뷰입니다.

    `RegisterCustomerView`와 동일한 방식으로 작동하며, 사용자 역할만 '점주'로 설정됩니다.
    """

    parser_classes: tuple[type[JSONParser], type[FormParser], type[MultiPartParser]] = (
        JSONParser,
        FormParser,
        MultiPartParser,
    )
    authentication_classes: tuple = ()

    def post(self, request: Request) -> Response:
        """
        새로운 점주 사용자를 생성합니다.
        `RegisterOwnerSerializer`를 사용해 요청 데이터를 검증하고, `OWNER` 역할을 할당합니다.
        """
        serializer = RegisterOwnerSerializer(
            data=request.data, context={"role": User.Role.OWNER}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            RegisterOwnerSerializer(user).data, status=status.HTTP_201_CREATED
        )


# ------------------------ 로그인 -------------------------
@extend_schema(
    tags=["Auth"],
    summary="로그인 (username 또는 email + password)",
    description="""
    `username` 또는 `email`과 `password`를 사용하여 로그인하고 JWT 토큰을 발급받습니다.
    요청 본문의 필드 이름은 `identifier` 또는 `username`입니다.
    - **요청 예시**: `{"identifier": "alice", "password": "..."}` 또는 `{"username": "alice", "password": "..."}`
    - **응답**: `access` 및 `refresh` 토큰
    """,
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
    auth=None,
)
class LoginView(TokenObtainPairView):
    """
    사용자 인증을 처리하고 JWT Access/Refresh 토큰을 발급하는 API 뷰입니다.

    `IdentifierTokenObtainPairSerializer`를 사용하여 `username` 또는 `email`로 로그인할 수 있도록 확장합니다.
    성공 시, 클라이언트는 `access`와 `refresh` 토큰을 응답으로 받게 됩니다.
    `access` 토큰은 보호된 API에 접근할 때 사용되며, `refresh` 토큰은 `access` 토큰이 만료되었을 때 재발급받는 데 사용됩니다.
    """

    authentication_classes: tuple = ()
    serializer_class = IdentifierTokenObtainPairSerializer


# ------------------------ Access 토큰 재발급 -------------------------
@extend_schema(
    tags=["Auth"],
    summary="Access 토큰 재발급",
    description="""
    만료된 Access 토큰 대신 Refresh 토큰을 사용하여 새로운 Access 토큰을 발급받습니다.
    """,
    request={"application/json": {"example": {"refresh": "your_refresh_token_here"}}},
    responses={
        200: {
            "description": "새로운 Access 토큰 발급",
            "content": {
                "application/json": {
                    "examples": {
                        "success": {
                            "value": {
                                "access": "new_access_token_here",
                                "refresh": "your_refresh_token_here",
                            }
                        }
                    }
                }
            },
        },
        401: {"description": "유효하지 않은 토큰"},
    },
    auth=None,
)
class RefreshView(TokenRefreshView):
    """
    JWT Access 토큰 재발급을 처리하는 API 뷰입니다.
    만료된 Access 토큰 대신 Refresh 토큰을 사용하여 새로운 Access 토큰을 받습니다.

    요청 본문(JSON):
        - `refresh`: 기존에 발급받은 Refresh 토큰
    """

    authentication_classes: tuple = ()
    pass


# ------------------------ 사용자 정보 조회 -------------------------
@extend_schema(
    tags=["Auth"],
    summary="내 프로필 조회 (로그인 필수))",
    description="""
    JWT Access 토큰을 사용하여 현재 로그인된 사용자의 기본 프로필 정보를 반환합니다.
    - 인증 방식 : `Authorization: Bearer <access_token>`
    - 응답 : 사용자가 손님이면 `favorite_locations`가, 점주면 `place` 정보가 포함됩니다.
    """,
    responses={
        200: MeSerializer,
        401: OpenApiExample(
            "인증 실패",
            value={"detail": "Authentication credentials were not provided."},
        ),
    },
)
class MeView(APIView):
    """
    현재 인증된 사용자의 프로필 정보를 반환하는 보호된 엔드포인트입니다.

    **GET 요청** 시 `MeSerializer`를 통해 직렬화된 사용자 데이터가 반환됩니다.
    이 뷰는 보통 프론트엔드에서 로그인 직후 사용자 정보를 가져오는 용도로 활용됩니다.
    """

    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """
        요청 헤더의 JWT를 통해 인증된 사용자의 정보를 반환합니다.
        """
        user: User = request.user  # type: ignore[assignment]
        serializer = MeSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ------------------------ 마이페이지 프로필 조회 및 수정 -------------------------
@extend_schema(
    tags=["User"],
    summary="내 프로필 조회 및 수정 (로그인 필수)",
    description="JWT Access 토큰을 사용하여 현재 로그인된 사용자의 프로필을 조회하고 수정합니다.",
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    마이페이지 프로필 조회 및 수정 뷰입니다.

    **GET 요청**: 현재 인증된 사용자의 프로필 정보를 조회합니다.
    **PUT/PATCH 요청**: 현재 인증된 사용자의 프로필 정보를 수정합니다.
    """

    serializer_class = UserUpdateSerializer
    permission_classes: list[type[IsAuthenticated]] = [permissions.IsAuthenticated]

    def get_object(self) -> AbstractUser | AnonymousUser:
        """
        현재 인증된 사용자 객체를 반환합니다.
        이를 통해 다른 사용자의 프로필을 조회하거나 수정하는 것을 방지합니다.
        """
        return self.request.user


# ------------------------ 로그아웃 -------------------------
@extend_schema(
    tags=["Auth"],
    summary="로그아웃",
    description="""
    사용자의 **Refresh 토큰을 블랙리스트에 추가**하여 무효화합니다.
    해당 토큰으로는 더 이상 Access 토큰을 재발급받을 수 없게 됩니다.
    """,
    request={
        "application/json": {"example": {"refresh_token": "your_refresh_token_here"}}
    },
    responses={
        200: {"description": "로그아웃 성공"},
        400: {"description": "유효하지 않은 토큰 또는 필수 필드 누락"},
    },
)
class LogoutView(APIView):
    """
    로그아웃을 처리하는 API 뷰입니다.
    클라이언트가 보낸 Refresh 토큰을 블랙리스트에 추가하여 무효화합니다.

    요청 본문(JSON):
        - `refresh_token`: 블랙리스트에 추가할 Refresh 토큰 (필수)

    이후 이 토큰으로는 더 이상 새로운 Access 토큰을 받을 수 없습니다.
    """

    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """
        Refresh 토큰을 블랙리스트에 추가하여 로그아웃 처리합니다.
        """
        try:
            refresh_token = request.data["refresh_token"]
            if not refresh_token:
                # `get()`을 사용하여 KeyError를 방지하고, 명확한 메시지 반환
                return Response(
                    {"detail": "refresh_token 필드가 필요합니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token = RefreshToken(refresh_token)

            token.blacklist()

            return Response(
                {"detail": "로그아웃되었습니다."}, status=status.HTTP_200_OK
            )

        except TokenError as e:
            # 토큰 유효성 검사 실패 시
            return Response(
                {"detail": f"유효하지 않은 토큰입니다: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except KeyError:
            # 'refresh_token' 필드가 없는 경우 KeyError 발생
            return Response(
                {"error": "refresh_token field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # 그 외의 모든 예외 처리
            return Response(
                {"detail": f"알 수 없는 오류가 발생했습니다: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


# ------------------------ 회원 탈퇴 -------------------------
@extend_schema(
    tags=["User"],
    summary="회원 탈퇴",
    description="JWT Access 토큰을 사용하여 현재 로그인된 사용자 계정을 삭제합니다. **삭제 후에는 복구할 수 없습니다.**",
    request=None,  # DELETE 요청은 body가 필요 없습니다.
    responses={
        204: {"description": "회원 탈퇴 성공 (No Content)"},
        401: {"description": "인증 실패"},
    },
)
class UserDeactivateView(generics.DestroyAPIView):
    """
    회원 탈퇴를 처리하는 API 뷰입니다.

    DELETE 요청 시, 현재 로그인된 사용자 계정을 비활성화(삭제)합니다.
    계정이 삭제되면 더 이상 로그인할 수 없게 됩니다.

    - 권장: DELETE /accounts/deactivate  (본문 JSON) {"password": "현재비번"}
    - 일부 클라이언트 제약 대응: ?password=... 쿼리스트링도 허용
    - 성공 시 204 No Content
    """

    # 로그인 상태에서만 접근 가능
    permission_classes: list[type[IsAuthenticated]] = [permissions.IsAuthenticated]

    def _blacklist_all_tokens(self, user: User) -> None:
        try:
            for outstanding in OutstandingToken.objects.filter(user=user):
                BlacklistedToken.objects.get_or_create(token=outstanding)
        except Exception:
            pass  # token_blacklist 미사용 시 무시

    def delete(self, request: Request) -> Response:
        password = (
            request.data.get("password") if isinstance(request.data, dict) else None
        )
        password = password or request.query_params.get("password")
        if not password:
            return Response(
                {"detail": "password가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        user: User = request.user  # type: ignore
        if not user.check_password(password):
            return Response(
                {"detail": "현재 비밀번호가 올바르지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self._blacklist_all_tokens(user)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # def get_object(self) -> AbstractUser | AnonymousUser:
    #     """
    #     현재 인증된 사용자 객체를 반환합니다.
    #     다른 사용자의 계정을 삭제하는 것을 방지합니다.
    #     """
    #     return self.request.user
