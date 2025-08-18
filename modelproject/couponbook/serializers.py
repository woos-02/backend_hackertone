from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema_field,
    extend_schema_serializer,
)
from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import *

# 시리얼라이저는 역순으로 정의되어 있습니다.

DATETIME_FORMAT = "%Y-%m-%d %H:%M"  # 기본 datetime 출력 포맷
TIME_FORMAT = "%H:%M"  # 기본 time 출력 포맷


# -------------------------- 스탬프 ----------------------------------
@extend_schema_serializer(examples=[OpenApiExample("예시", {"receipt": "01234567890"})])
# class StampListRequestSerializer(serializers.ModelSerializer):
#     """
#     스탬프를 생성(적립)하는 데에 사용되는 시리얼라이저입니다. 입력받은 영수증 번호를 바탕으로 스탬프를 생성합니다.
#     """

#     def validate(self, data) -> dict:
#         """
#         1. 영수증 번호가 등록되어 있는 영수증인지 확인합니다.
#         2. 영수증 번호에 해당하는 스탬프가 이미 등록되어 있는지 확인합니다.

#         둘 중 하나라도 만족하지 못하면 ValidationError가 발생합니다.
#         """
#         receipt = data.get("receipt")
#         if not receipt:
#             raise serializers.ValidationError("DB에 등록되지 않은 영수증 번호입니다.")

#         if hasattr(receipt, "stamp"):
#             raise serializers.ValidationError("이미 스탬프가 발급된 영수증 번호입니다.")

#         return super().validate(data)

#     def create(self, validated_data) -> Stamp:
#         """
#         유효성 검증을 통과한 영수증 번호를 바탕으로 쿠폰 id와 유저를 바탕으로 스탬프 인스턴스를 생성하고 돌려줍니다.
#         """
#         receipt = validated_data.pop("receipt")
#         coupon_id = self.context["coupon_id"]
#         user = self.context["request"].user

#         return Stamp.objects.create(receipt=receipt, coupon_id=coupon_id, customer=user)

#     class Meta:
#         model = Stamp
#         fields = ["receipt"]
class StampListRequestSerializer(serializers.ModelSerializer):
    """
    영수증 번호 문자열을 받아 Receipt를 조회/자동 생성 후 Stamp를 만듭니다.
    """
    receipt_number = serializers.CharField(write_only=True)

    class Meta:
        model = Stamp
        fields = ["receipt_number"]

    def validate(self, data):
        num = data.get("receipt_number")
        if not num:
            raise serializers.ValidationError({"receipt_number": "영수증 번호가 필요합니다."})
        # 정책 1: 없는 번호는 자동 생성
        receipt, _ = Receipt.objects.get_or_create(receipt_number=num)
        # 정책 2: 이미 사용된 영수증이면 거절
        if hasattr(receipt, "stamp"):
            raise serializers.ValidationError({"receipt_number": "이미 스탬프가 발급된 영수증 번호입니다."})
        data["receipt"] = receipt
        return data

    def create(self, validated_data):
        validated_data.pop("receipt_number", None)
        receipt = validated_data.pop("receipt")
        coupon_id = self.context["coupon_id"]
        user = self.context["request"].user
        return Stamp.objects.create(receipt=receipt, coupon_id=coupon_id, customer=user)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "예시", {"id": 1, "stamp_url": "http://localhost:8000/couponbook/stamps/1"}
        )
    ]
)
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
        request = self.context["request"]
        return reverse(
            "couponbook:stamp-detail", kwargs={"stamp_id": obj.id}, request=request
        )

    class Meta:
        model = Stamp
        fields = ["id", "stamp_url"]


@extend_schema_serializer(
    examples=[OpenApiExample("예시", {"id": 1, "created_at": "2025-08-18 21:00"})]
)
class StampDetailResponseSerializer(serializers.ModelSerializer):
    """
    한 스탬프의 정보를 조회하는 응답에 사용되는 시리얼라이저입니다.
    """

    created_at = serializers.DateTimeField(DATETIME_FORMAT)

    class Meta:
        model = Stamp
        fields = ["id", "created_at"]


# ------------------------ 혜택 정보 ---------------------------
@extend_schema_serializer(
    examples=[OpenApiExample("예시", {"amount": 10, "reward": "아메리카노 1잔 무료"})]
)
class RewardsInfoDetailSerializer(serializers.ModelSerializer):
    """
    쿠폰에 해당하는 혜택 정보를 조회하는 시리얼라이저입니댜.
    """

    class Meta:
        model = RewardsInfo
        exclude = ["id", "coupon_template"]


# ---------------------------- 가게 ---------------------------------------
@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "예시",
            {
                "id": 1,
                "name": "매머드 커피",
                "address": "서울 동대문구 이문동 264-223",
                "image_url": "http://localhost:8000",
                "opens_at": "08:00",
                "closes_at": "21:00",
                "last_order": "20:30",
                "tel": "0507-1361-0962",
            },
        )
    ]
)
class PlaceDetailResponseSerializer(serializers.ModelSerializer):
    """
    가게 정보를 조회하는 응답에 사용되는 시리얼라이저입니다.
    """

    opens_at = serializers.TimeField(TIME_FORMAT)
    closes_at = serializers.TimeField(TIME_FORMAT)
    last_order = serializers.TimeField(TIME_FORMAT)

    class Meta:
        model = Place
        fields = "__all__"


# 여기 추가
class PlaceSerializer(serializers.ModelSerializer):
    """
    가게(Place) 정보를 조회할 때 사용하는 시리얼라이저입니다.
    """

    class Meta:
        model = Place
        fields = ["id", "name", "address", "opens_at", "closes_at", "last_order", "tel"]


class PlaceCreateSerializer(serializers.ModelSerializer):
    """
    가게를 생성할 때 사용하는 시리얼라이저입니다.
    """

    class Meta:
        model = Place
        # owner 필드는 accounts/serializers.py에서 자동으로 처리
        fields = ["name", "address", "image_url", "opens_at", "closes_at", "last_order", "tel"]


# ------------------------ 쿠폰 템플릿 -------------------------
@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "예시",
            {
                "id": 1,
                "max_stamps": 10,
                "saves": 5,
                "uses": 2,
                "valid_until": "2025-11-11 23:59",
                "first_n_persons": 50,
                "is_on": True,
                "views": 8,
                "created_at": "2025-08-18 21:30",
            },
        )
    ]
)
class CouponTemplateListSerializer(serializers.ModelSerializer):
    """
    점주가 등록하여 게시중인 쿠폰 템플릿을 조회하는 시리얼라이저입니다.
    """

    place = PlaceDetailResponseSerializer()
    reward_info = RewardsInfoDetailSerializer()
    max_stamps = serializers.SerializerMethodField()
    saves = serializers.SerializerMethodField()
    uses = serializers.SerializerMethodField()
    valid_until = serializers.DateTimeField(DATETIME_FORMAT, allow_null=True, required=False)
    created_at = serializers.DateTimeField(DATETIME_FORMAT)

    def get_max_stamps(self, obj: CouponTemplate) -> int:
        """
        리워드를 받을 수 있는 스탬프 개수입니다.
        """
        reward_info = getattr(obj, "reward_info", None)
        return reward_info.amount if reward_info else 0

    def get_saves(self, obj: CouponTemplate) -> int:
        """
        유저 전체의 쿠폰북 기준으로 해당 쿠폰 템플릿으로 생성한 실사용 쿠폰이 저장되어 있는 횟수입니다.
        """
        saved_coupons = Coupon.objects.filter(original_template=obj)
        return saved_coupons.count()

    def get_uses(self, obj: CouponTemplate) -> int:
        """
        해당 쿠폰 템플릿으로 생성한 실사용 쿠폰으로 적립된 스탬프의 개수입니다.
        """
        saved_coupons = Coupon.objects.filter(original_template=obj)
        uses = 0
        for coupon in saved_coupons:
            uses += coupon.stamps.count()
        return uses

    class Meta:
        model = CouponTemplate
        fields = "__all__"


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "예시",
            {
                "id": 1,
                "max_stamps": 10,
                "current_n_remaining": 45,
                "valid_until": "2025-11-11 23:59",
                "first_n_persons": 50,
                "created_at": "2025-08-18 21:30",
            },
        )
    ]
)
class CouponTemplateDetailSerializer(serializers.ModelSerializer):
    """
    개별 쿠폰 템플릿을 조회하는 응답에 사용되는 시리얼라이저입니다.
    """

    reward_info = RewardsInfoDetailSerializer()
    max_stamps = serializers.SerializerMethodField()
    current_n_remaining = serializers.SerializerMethodField()
    valid_until = serializers.DateTimeField(DATETIME_FORMAT, allow_null=True, required=False)
    place = PlaceDetailResponseSerializer()
    created_at = serializers.DateTimeField(DATETIME_FORMAT)

    def get_max_stamps(self, obj: CouponTemplate) -> int:
        """
        리워드를 받을 수 있는 스탬프 개수입니다.
        """
        reward_info = getattr(obj, "reward_info", None)
        return reward_info.amount if reward_info else 0

    def get_current_n_remaining(self, obj: CouponTemplate) -> int:
        """
        현재 기준으로 쿠폰을 발급받을 수 있는 인원 수입니다.
        """
        coupons = obj.coupons
        return max(0, obj.first_n_persons - coupons.count()) # current_n_remaining 이 음수가 될 수 있어 0으로 바닥 고정

    class Meta:
        model = CouponTemplate
        exclude = ["is_on", "views"]


"""여기 추가"""


class CouponTemplateCreateSerializer(serializers.ModelSerializer):
    """
    점주가 새로운 쿠폰 템플릿을 등록할 때 사용하는 시리얼라이저입니다.
    `place` 필드는 뷰에서 현재 로그인된 점주와 연결된 가게 정보로 자동 할당됩니다.
    """

    reward_info = RewardsInfoDetailSerializer(write_only=True, required=True)
    valid_until = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = CouponTemplate
        # place 필드는 뷰에서 처리하므로 제외
        exclude = ["id", "place", "views", "created_at"]

    def create(self, validated_data):
        reward = validated_data.pop("reward_info")  # required=True 이므로 존재 보장
        template = CouponTemplate.objects.create(**validated_data)
        RewardsInfo.objects.create(coupon_template=template, **reward)
        return template

# --------------------------- 쿠폰 -----------------------------
@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "예시",
            {
                "original_template": 1,
            },
        )
    ]
)
class CouponListRequestSerializer(serializers.ModelSerializer):
    """
    쿠폰을 생성하는 데에 사용되는 시리얼라이저입니다.
    """

    def validate(self, data) -> dict:
        """
        1. 원본 쿠폰 템플릿이 존재하는지 확인합니다.
        2. 이미 해당 유저가 해당 쿠폰 템플릿으로 등록한 쿠폰이 존재하는지 확인합니다.
        """
        original_template = data.get("original_template")
        if not original_template:
            raise serializers.ValidationError("해당 쿠폰 템플릿이 존재하지 않습니다.")

        couponbook = self.context["couponbook"]
        coupon = Coupon.objects.filter(
            couponbook=couponbook, original_template=original_template
        )

        if coupon.exists():
            raise serializers.ValidationError(
                "이미 해당 쿠폰 템플릿으로 생성한 쿠폰이 존재합니다."
            )

        return super().validate(data)

    def create(self, validated_data) -> Coupon:
        """
        원본 쿠폰 템플릿을 바탕으로 실사용 쿠폰을 생성합니다.
        """
        original_template = validated_data.pop("original_template")
        couponbook = self.context["couponbook"]

        return Coupon.objects.create(
            couponbook=couponbook, original_template=original_template
        )

    class Meta:
        model = Coupon
        fields = ["original_template"]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "예시",
            {
                "id": 1,
                "coupon_url": "http://localhost:8000/couponbook/coupons/1",
                "is_favorite": True,
                "is_completed": False,
                "is_expired": False,
                "days_remaining": 7,
                "saved_at": "2025-08-18 21:35",
                "couponbook": 1,
            },
        )
    ]
)
class CouponListResponseSerializer(serializers.ModelSerializer):
    """
    쿠폰의 목록을 조회하는 응답에 사용되는 시리얼라이저입니다.
    """

    coupon_url = serializers.SerializerMethodField()
    place = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    saved_at = serializers.DateTimeField(DATETIME_FORMAT)

    @extend_schema_field(OpenApiTypes.URI)
    def get_coupon_url(self, obj: Coupon):
        """
        개별 쿠폰의 URL입니다.
        """
        request = self.context["request"]
        return reverse(
            "couponbook:coupon-detail", kwargs={"coupon_id": obj.id}, request=request
        )

    def get_place(self, obj: Coupon) -> PlaceDetailResponseSerializer:
        """
        해당 쿠폰과 연관된 가게 정보입니다.
        """
        original_template = obj.original_template
        place = original_template.place
        return PlaceDetailResponseSerializer(place).data

    def get_is_favorite(self, obj: Coupon) -> bool:
        """
        해당 쿠폰을 즐겨찾기에 등록했는지의 여부입니다.
        """
        user = self.context["request"].user
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
        valid_until = obj.original_template.valid_until
        return bool(valid_until and valid_until< now())

    def get_days_remaining(self, obj: Coupon) -> int:
        """
        해당 쿠폰의 유효기간이 며칠 남아 있는지를 의미합니다.
        """
        valid_until = obj.original_template.valid_until
        if not valid_until:
            return None
        return (valid_until - now()).days

    class Meta:
        model = Coupon
        exclude = ["original_template"]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "예시",
            {
                "id": 1,
                "saved_at": "2025-08-18 21:35",
                "couponbook": 1,
            },
        )
    ]
)
class CouponDetailResponseSerializer(serializers.ModelSerializer):
    """
    개별 쿠폰을 조회하는 응답에 사용되는 시리얼라이저입니다. 스탬프가 포함됩니다.
    """

    saved_at = serializers.DateTimeField(DATETIME_FORMAT)
    stamps = StampListResponseSerializer(many=True)

    class Meta:
        model = Coupon
        exclude = ["original_template"]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "예시",
            {
                "coupon": 1,
            },
        )
    ]
)
class FavoriteCouponListRequestSerializer(serializers.ModelSerializer):
    """
    쿠폰을 즐겨찾기를 등록할 때 사용되는 시리얼라이저입니다.
    """

    def validate(self, data) -> dict:
        """
        1. 해당 쿠폰 id에 해당하는 쿠폰이 존재하는지 확인합니다.
        2. 해당 쿠폰북에 해당 쿠폰이 즐겨찾기로 등록되어 있는지 확인합니다.
        """
        coupon = data.get("coupon")

        if not coupon:
            raise serializers.ValidationError(
                "쿠폰 id에 해당하는 쿠폰이 존재하지 않습니다."
            )

        couponbook = self.context["couponbook"]
        favorite_coupon = couponbook.favorite_coupons.filter(coupon=coupon)

        if favorite_coupon.exists():
            raise serializers.ValidationError("이미 즐겨찾기 등록된 쿠폰입니다.")

        return super().validate(data)

    def create(self, validated_data) -> FavoriteCoupon:
        """
        쿠폰 id에 해당하는 쿠폰을 현재 유저의 쿠폰북에 즐겨찾기 쿠폰으로 등록합니다.
        """
        coupon = validated_data.pop("coupon")
        couponbook = self.context["couponbook"]
        return FavoriteCoupon.objects.create(coupon=coupon, couponbook=couponbook)

    class Meta:
        model = FavoriteCoupon
        fields = ["coupon"]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "예시",
            {
                "id": 1,
                "added_at": "2025-08-18 21:40",
            },
        )
    ]
)
class FavoriteCouponListResponseSerializer(serializers.ModelSerializer):
    """
    즐겨찾기 등록한 쿠폰을 조회하는 응답에 사용되는 시리얼라이저입니다.
    """

    coupon = CouponDetailResponseSerializer()
    added_at = serializers.DateTimeField(DATETIME_FORMAT)

    class Meta:
        model = FavoriteCoupon
        exclude = ["couponbook"]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "예시",
            {
                "id": 1,
                "added_at": "2025-08-18 21:40",
                "coupon": 1,
            },
        )
    ]
)
class FavoriteCouponDetailResponseSerializer(serializers.ModelSerializer):
    """
    FavoriteCouponDetailView의 serializer_class로 지정하기 위해 만든 시리얼라이저입니다. 실제로 조회 응답에 사용되진 않습니다.
    """

    added_at = serializers.DateTimeField(DATETIME_FORMAT)

    class Meta:
        model = FavoriteCoupon
        exclude = ["couponbook"]


# -------------------------- 쿠폰북 ----------------------------
@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "예시",
            {
                "id": 1,
                "favorite_counts": 1,
                "coupon_counts": 1,
                "stamp_counts": 1,
                "user": 1,
            },
        )
    ]
)
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
        user = self.context["request"].user
        stamps = Stamp.objects.filter(customer=user)
        return stamps.count()

    class Meta:
        model = CouponBook
        fields = "__all__"
