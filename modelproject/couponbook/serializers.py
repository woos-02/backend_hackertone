from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import *

# 시리얼라이저는 역순으로 정의되어 있습니다.

# -------------------------- 스탬프 ----------------------------------
class StampListRequestSerializer(serializers.ModelSerializer):
    """
    스탬프를 생성(적립)하는 데에 사용되는 시리얼라이저입니다. 입력받은 영수증 번호를 바탕으로 스탬프를 생성합니다.
    """

    def validate(self, data) -> dict:
        """
        1. 영수증 번호가 등록되어 있는 영수증인지 확인합니다.
        2. 영수증 번호에 해당하는 스탬프가 이미 등록되어 있는지 확인합니다.

        둘 중 하나라도 만족하지 못하면 ValidationError가 발생합니다.
        """
        receipt = data.get('receipt')
        if not receipt:
            raise serializers.ValidationError("DB에 등록되지 않은 영수증 번호입니다.")
        
        if hasattr(receipt, 'stamp'):
            raise serializers.ValidationError("이미 스탬프가 발급된 영수증 번호입니다.")

        return super().validate(data)
    
    def create(self, validated_data) -> Stamp:
        """
        유효성 검증을 통과한 영수증 번호를 바탕으로 쿠폰 id와 유저를 바탕으로 스탬프 인스턴스를 생성하고 돌려줍니다.
        """
        receipt = validated_data.pop('receipt')
        coupon_id = self.context['coupon_id']
        user = self.context['request'].user

        return Stamp.objects.create(receipt=receipt, coupon_id=coupon_id, customer=user)
    
    class Meta:
        model = Stamp 
        fields = ['receipt']


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
        return reverse('couponbook:stamp-detail', kwargs={'stamp_id': obj.id}, request=request)
    
    class Meta:
        model = Stamp
        fields = ['id', 'stamp_url']

class StampDetailResponseSerializer(serializers.ModelSerializer):
    """
    한 스탬프의 정보를 조회하는 응답에 사용되는 시리얼라이저입니다.
    """
    class Meta:
        model = Stamp
        fields = ['id', 'created_at']


# ------------------------ 혜택 정보 ---------------------------
class RewardsInfoDetailSerializer(serializers.ModelSerializer):
    """
    쿠폰에 해당하는 혜택 정보를 조회하는 시리얼라이저입니댜.
    """
    class Meta:
        model = RewardsInfo
        exclude = ['id', 'coupon_template']


# ------------------------ 쿠폰 템플릿 -------------------------
class CouponTemplateListSerializer(serializers.ModelSerializer):
    """
    점주가 등록하여 게시중인 쿠폰 템플릿을 조회하는 시리얼라이저입니다.
    """
    reward_info = RewardsInfoDetailSerializer()

    class Meta:
        model = CouponTemplate
        fields = '__all__'

class CouponTemplateDetailSerializer(serializers.ModelSerializer):
    """
    개별 쿠폰 템플릿을 조회하는 응답에 사용되는 시리얼라이저입니다.
    """
    reward_info = RewardsInfoDetailSerializer()

    class Meta:
        model = CouponTemplate
        exclude = ['is_on', 'views', 'saves', 'uses']


# --------------------------- 쿠폰 -----------------------------
class CouponListRequestSerializer(serializers.ModelSerializer):
    """
    쿠폰을 생성하는 데에 사용되는 시리얼라이저입니다.
    """

    def validate(self, data) -> dict:
        """
        1. 원본 쿠폰 템플릿이 존재하는지 확인합니다.
        2. 이미 해당 유저가 해당 쿠폰 템플릿으로 등록한 쿠폰이 존재하는지 확인합니다.
        """
        original_template = data.get('original_template')
        if not original_template:
            raise serializers.ValidationError("해당 쿠폰 템플릿이 존재하지 않습니다.")
        
        couponbook = self.context['couponbook']
        coupon = Coupon.objects.filter(couponbook=couponbook, original_template=original_template)

        if coupon.exists():
            raise serializers.ValidationError("이미 해당 쿠폰 템플릿으로 생성한 쿠폰이 존재합니다.")
        
        return super().validate(data)
    
    def create(self, validated_data) -> Coupon:
        """
        원본 쿠폰 템플릿을 바탕으로 실사용 쿠폰을 생성합니다.
        """
        original_template = validated_data.pop('original_template')
        couponbook = self.context['couponbook']
        
        return Coupon.objects.create(couponbook=couponbook, original_template=original_template)
            

    class Meta:
        model = Coupon
        fields = ['original_template']

class CouponListResponseSerializer(serializers.ModelSerializer):
    """
    쿠폰의 목록을 조회하는 응답에 사용되는 시리얼라이저입니다.
    """
    coupon_url = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.URI)
    def get_coupon_url(self, obj: Coupon):
        """
        개별 쿠폰의 URL입니다.
        """
        request = self.context['request']
        return reverse('couponbook:coupon-detail', kwargs={'coupon_id': obj.id}, request=request)
    
    def get_is_favorite(self, obj: Coupon) -> bool:
        """
        해당 쿠폰을 즐겨찾기에 등록했는지의 여부입니다.
        """
        user = self.context['request'].user
        couponbook = CouponBook.objects.get(user=user)
        favorite_coupon = couponbook.favorite_coupons.filter(coupon=obj)

        return favorite_coupon.exists()
    
    def get_is_completed(self, obj: Coupon) -> bool:
        """
        해당 쿠폰이 완성되었는지를 의미합니다.
        """
        original_template: CouponTemplate = obj.original_template
        reward_info: RewardsInfo = original_template.reward_info
        max_stamps: int = reward_info.amount
        current_stamps: int = Stamp.objects.filter(coupon=obj).count()

        return max_stamps == current_stamps
    
    def get_is_expired(self, obj: Coupon) -> bool:
        """
        해당 쿠폰의 유효기간이 만료되었는지를 의미합니다.
        """
        original_template: CouponTemplate = obj.original_template
        valid_until = original_template.valid_until
        return valid_until < now()

        
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

class FavoriteCouponListRequestSerializer(serializers.ModelSerializer):
    """
    쿠폰을 즐겨찾기를 등록할 때 사용되는 시리얼라이저입니다.
    """
    def validate(self, data) -> dict:
        """
        1. 해당 쿠폰 id에 해당하는 쿠폰이 존재하는지 확인합니다.
        2. 해당 쿠폰북에 해당 쿠폰이 즐겨찾기로 등록되어 있는지 확인합니다.
        """
        coupon = data.get('coupon')

        if not coupon:
            raise serializers.ValidationError("쿠폰 id에 해당하는 쿠폰이 존재하지 않습니다.")
        
        couponbook = self.context['couponbook']
        favorite_coupon = couponbook.favorite_coupons.filter(coupon=coupon)

        if favorite_coupon.exists():
            raise serializers.ValidationError("이미 즐겨찾기 등록된 쿠폰입니다.")

        return super().validate(data)
    
    def create(self, validated_data) -> FavoriteCoupon:
        """
        쿠폰 id에 해당하는 쿠폰을 현재 유저의 쿠폰북에 즐겨찾기 쿠폰으로 등록합니다.
        """
        coupon = validated_data.pop('coupon')
        couponbook = self.context['couponbook']
        return FavoriteCoupon.objects.create(coupon=coupon, couponbook=couponbook)

    class Meta:
        model = FavoriteCoupon
        fields = ['coupon']

class FavoriteCouponListResponseSerializer(serializers.ModelSerializer):
    """
    즐겨찾기 등록한 쿠폰을 조회하는 응답에 사용되는 시리얼라이저입니다.
    """
    coupon = CouponDetailResponseSerializer()

    class Meta:
        model = FavoriteCoupon
        exclude = ['couponbook']

class FavoriteCouponDetailResponseSerializer(serializers.ModelSerializer):
    """
    FavoriteCouponDetailView의 serializer_class로 지정하기 위해 만든 시리얼라이저입니다. 실제로 조회 응답에 사용되진 않습니다.
    """
    class Meta:
        model = FavoriteCoupon
        exclude = ['couponbook']


# -------------------------- 쿠폰북 ----------------------------
class CouponBookResponseSerializer(serializers.ModelSerializer):
    """
    쿠폰북을 조회하는 응답에 사용되는 시리얼라이저입니다.
    """
    favorite_counts = serializers.SerializerMethodField()
    coupon_counts = serializers.SerializerMethodField()
    stamp_counts = serializers.SerializerMethodField()

    def get_favorite_counts(self, obj: CouponBook) -> int:
        """
        즐겨찾기 한 쿠폰의 개수입니다.
        """
        coupons = FavoriteCoupon.objects.filter(couponbook=obj)
        return coupons.count()
    
    def get_coupon_counts(self, obj: CouponBook) -> int:
        """
        쿠폰북에 등록한 쿠폰의 개수입니다.
        """
        coupons = Coupon.objects.filter(couponbook=obj)
        return coupons.count()
    
    def get_stamp_counts(self, obj: CouponBook) -> int:
        """
        지금까지 적립한 스탬프의 개수입니다.
        """
        user = self.context['request'].user
        stamps = Stamp.objects.filter(customer=user)
        return stamps.count()

    class Meta:
        model = CouponBook
        fields = '__all__'