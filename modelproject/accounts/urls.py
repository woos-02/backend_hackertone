"""
Accounts 앱 URLConf.

이 파일은 `urls.py` 파일로, `accounts` 앱의 URL 라우팅을 담당합니다.
프로젝트의 메인 `urls.py`에서 `path("accounts/", include("accounts.urls"))`와 같이
포함되는 것을 전제로 합니다.

즉, 각 엔드포인트의 전체 경로는 다음과 같습니다:
- 손님 회원가입: POST /accounts/auth/register/customer
- 점주 회원가입: POST /accounts/auth/register/owner
- 로그인: POST /accounts/auth/login
- 로그아웃: POST /accounts/auth/logout
- 토큰 재발급: POST /accounts/auth/refresh
- 내 프로필 조회: GET /accounts/auth/me
- 마이페이지 프로필 수정: PUT/PATCH /accounts/profile
- 회원 탈퇴: POST /accounts/deactivate
"""

from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    MeView,
    RefreshView,
    RegisterCustomerView,
    RegisterOwnerView,
    UserDeactivateView,
    UserProfileView,
)

app_name = "accounts"

urlpatterns: list = [
    path(
        "auth/register/customer/",
        RegisterCustomerView.as_view(),
        name="register-customer/",
    ),  # 손님 회원가입
    path(
        "auth/register/owner/", RegisterOwnerView.as_view(), name="register-owner"
    ),  # 점주 회원가입
    path("auth/login/", LoginView.as_view(), name="login"),  # 로그인
    path("auth/logout/", LogoutView.as_view(), name="logout"),  # 로그아웃
    path("auth/refresh/", RefreshView.as_view(), name="refresh"),  # Access 토큰 재발급
    path(
        "deactivate/", UserDeactivateView.as_view(), name="user-deactivate"
    ),  # 회원 탈퇴
    path("auth/me/", MeView.as_view(), name="me"),  # 신규 보호 엔드포인트
    path(
        "profile/", UserProfileView.as_view(), name="user-profile"
    ),  # 마이페이지 프로필 조회/수정
]
