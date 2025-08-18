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
        "auth/register/customer",
        RegisterCustomerView.as_view(),
        name="register-customer",
    ),  # 손님 회원가입
    path(
        "auth/register/owner", RegisterOwnerView.as_view(), name="register-owner"
    ),  # 점주 회원가입
    path("auth/login", LoginView.as_view(), name="login"),  # 로그인
    path("auth/logout", LogoutView.as_view(), name="logout"),  # 로그아웃
    path(
        "deactivate", UserDeactivateView.as_view(), name="user-deactivate"
    ),  # 회원 탈퇴
    path("auth/refresh", RefreshView.as_view(), name="refresh"),  # Refresh 발급
    path("auth/me", MeView.as_view()),  # 신규 보호 엔드포인트
    path(
        "profile", UserProfileView.as_view(), name="user-profile"
    ),  # 마이페이지 프로필 조회/수정
]
