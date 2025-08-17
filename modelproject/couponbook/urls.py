from django.urls import path

from .views import *

app_name = 'couponbook'

urlpatterns = [
    # 로그인한 유저의 쿠폰북을 조회하는 URL에서 시작합니다.
    path('own-couponbook/', CouponBookDetailView.as_view(), name='user-own-couponbook'),
    path('couponbooks/<int:couponbook_id>/coupons/', CouponListView.as_view(), name='coupon-list'),
    path('coupons/<int:coupon_id>/', CouponDetailView.as_view(), name='coupon-detail'),
    path('coupons/<int:coupon_id>/stamps/', StampListView.as_view(), name='stamp-list'),
    path('coupon-templates/', CouponTemplateListView.as_view(), name='coupon-template-list'),
    path('coupon-templates/<int:coupon_template_id>/', CouponTemplateDetailView.as_view(), name='coupon-template-detail'),
]