from django.contrib import admin
from django.db import models

from .models import (Coupon, CouponBook, CouponTemplate, FavoriteCoupon,
                     LegalDistrict, Place, Receipt, RewardsInfo, Stamp)


# CouponBook 모델을 Django 관리자 페이지에 등록
@admin.register(CouponBook)
class CouponBookAdmin(admin.ModelAdmin):
    # 'design_json' 필드가 모델에서 제거되었으므로 list_display에서 삭제합니다.
    list_display = (
        "id",
        "user",
    )
    list_display_links = ("id", "user")


# Coupon 모델을 Django 관리자 페이지에 등록
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "couponbook",
        "original_template",
    )
    search_fields = ("couponbook__user__username", "original_template__id")

# FavoriteCoupon 모델을 Django 관리자 페이지에 등록
@admin.register(FavoriteCoupon)
class FavoriteCouponAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'coupon',
        'couponbook',
        'added_at',
    )
    search_fields = ('id', 'coupon', 'couponbook')


# CouponTemplate 모델을 Django 관리자 페이지에 등록
@admin.register(CouponTemplate)
class CouponTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "valid_until",
        "is_on",
        "created_at",
    )
    list_filter = ("is_on",)
    search_fields = ("valid_until",)


# RewardsInfo 모델을 Django 관리자 페이지에 등록
@admin.register(RewardsInfo)
class RewardsInfoAdmin(admin.ModelAdmin):
    list_display = ("id", "coupon_template", "amount", "reward")
    search_fields = ("coupon_template__id",)


# Stamp 모델을 Django 관리자 페이지에 등록
@admin.register(Stamp)
class StampAdmin(admin.ModelAdmin):
    # 'related_payment' 대신 'receipt_number' 필드를 사용하도록 수정합니다.
    list_display = ("id", "coupon", "customer", "receipt", "created_at")
    list_filter = ("customer",)
    search_fields = (
        "coupon__id",
        "customer__username",
        "receipt__receipt_number",
    )


# Receipt 모델을 Django 관리자 페이지에 등록
@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "created_at")
    search_fields = ("receipt_number",)

@admin.register(LegalDistrict)
class LegalDistrictAdmin(admin.ModelAdmin):
    list_display = ("code_in_law", "province", "city", "district")

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "address_district", "address_rest", "tel")
    search_fields = ("id", "name", "address_district", "tel")
    