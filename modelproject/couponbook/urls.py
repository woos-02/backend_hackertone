from django.urls import path

from .views import (
    CouponBookDetailView, CouponListView, CouponDetailView, CouponCurationView,
    FavoriteCouponListView, FavoriteCouponDetailView,
    StampListView, StampDetailView,
    CouponTemplateListView, CouponTemplateDetailView,
    PlaceListView)

app_name = 'couponbook'

urlpatterns = [
    # 로그인한 유저의 쿠폰북을 조회하는 URL에서 시작합니다.
    path('own-couponbook/', CouponBookDetailView.as_view(), name='user-own-couponbook'),
    path('couponbooks/<int:couponbook_id>/coupons/', CouponListView.as_view(), name='coupon-list'),
    path('coupons/<int:coupon_id>/', CouponDetailView.as_view(), name='coupon-detail'),
    path('own-couponbook/curation/', CouponCurationView.as_view(), name='coupon-curation'),
    path('couponbooks/<int:couponbook_id>/favorites/', FavoriteCouponListView.as_view(), name='favorite-coupon-list'),
    path('own-couponbook/favorites/<int:favorite_id>/', FavoriteCouponDetailView.as_view(), name='favorite-coupon-detail'),
    path('coupons/<int:coupon_id>/stamps/', StampListView.as_view(), name='stamp-list'),
    path('stamps/<int:pk>/', StampDetailView.as_view(), name='stamp-detail'),

    # 쿠폰 템플릿 관련 엔드포인트입니다.
    path('coupon-templates/', CouponTemplateListView.as_view(), name='coupon-template-list'),
    path('coupon-templates/<int:coupon_template_id>/', CouponTemplateDetailView.as_view(), name='coupon-template-detail'),

    # 가게 검색
    path('places/', PlaceListView.as_view(), name='place-list'),
]