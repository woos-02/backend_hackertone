from django.urls import path

from .views import RegisterCustomerView, RegisterOwnerView, LoginView, RefreshView

app_name = "accounts"

urlpatterns = [
    path("auth/register/customer", RegisterCustomerView.as_view(), name="register-customer"),
    path("auth/register/owner", RegisterOwnerView.as_view(), name="register-owner"),
    path("auth/login", LoginView.as_view(), name="login"),
    path("auth/refresh", RefreshView.as_view(), name="refresh"),
]
