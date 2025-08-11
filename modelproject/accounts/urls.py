from django.urls import path
from .views import RegisterCustomerView, RegisterOwnerView, LoginView, RefreshView, MeView

app_name = "accounts"

urlpatterns = [
    path("auth/register/customer", RegisterCustomerView.as_view(), name="register-customer"), # 손님 회원가입
    path("auth/register/owner", RegisterOwnerView.as_view(), name="register-owner"), # 점주 회원가입
    path("auth/login", LoginView.as_view(), name="login"), # 로그인
    path("auth/refresh", RefreshView.as_view(), name="refresh"), # Refresh 발급
    path("auth/me", MeView.as_view()) # 신규 보호 엔드포인트
]