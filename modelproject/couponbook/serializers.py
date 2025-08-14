from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import *

# 시리얼라이저는 역순으로 정의되어 있습니다.

# -------------------------- 스탬프 ----------------------------------
class StampListResponseSerializer(serializers.ModelSerializer):
    """
    스탬프의 목록을 조회하는 응답에 사용되는 시리얼라이저입니다.
    """
    stamp_url = serializers.SerializerMethodField()
    
    @extend_schema_field(OpenApiTypes.URI)
    def get_stamp_url(self, obj: Stamp):
        """
        개별 스탬프의 URL입니다.
        """
        request = self.context['request']
        reverse('couponbook:stamp-detail', kwargs={'stamp_id': obj.id}, request=request)
    
    class Meta:
        model = Stamp
        fields = ['id', 'stamp_url']


# --------------------------- 쿠폰 -----------------------------
class CouponListResponseSerializer(serializers.ModelSerializer):
    """
    쿠폰의 목록을 조회하는 응답에 사용되는 시리얼라이저입니다.
    """
    coupon_url = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.URI)
    def get_coupon_url(self, obj: Coupon):
        """
        개별 쿠폰의 URL입니다.
        """
        request = self.context['request']
        reverse('couponbook:coupon-detail', kwargs={'couponbook_id': obj.id}, request=request)
        
    class Meta:
        model = Coupon
        exclude = ['original_template']

class CouponDetailResponseSerializer(serializers.ModelSerializer):
    """
    개별 쿠폰을 조회하는 응답에 사용되는 시리얼라이저입니다. 스탬프가 포함됩니다.
    """
    stamps = StampListResponseSerializer(many=True)

    class Meta:
        model = Coupon
        exclude = ['original_template']


# -------------------------- 쿠폰북 ----------------------------
class CouponBookResponseSerializer(serializers.ModelSerializer):
    """
    쿠폰북을 조회하는 응답에 사용되는 시리얼라이저입니다.
    """
    class Meta:
        model = CouponBook
        fields = '__all__'