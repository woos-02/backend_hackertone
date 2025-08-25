from django.utils.timezone import now
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, extend_schema_field,
                                   extend_schema_serializer)
from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import *

# 시리얼라이저는 역순으로 정의되어 있습니다.

DATETIME_FORMAT = "%Y-%m-%d %H:%M"  # 기본 datetime 출력 포맷
TIME_FORMAT = "%H:%M"  # 기본 time 출력 포맷


# -------------------------- 스탬프 적립 ----------------------------------
@extend_schema_serializer(
    examples=[
        OpenApiExample("예시", {"receipt_number": "01234567890"})
    ]
)
class StampCreateRequestSerializer(serializers.ModelSerializer):
    """
    스탬프를 생성(적립)하는 데에 사용되는 시리얼라이저입니다. 입력받은 영수증 번호를 바탕으로 스탬프를 생성합니다.
    """

    def validate(self, attrs) -> dict:
        """
        쿠폰 확인, 영수증 확인을 거쳐 스탬프 적립의 유효성을 검증합니다.

        유효하지 않으면 ValidationError가 일어납니다.
        """
        
        # 쿠폰 확인
        coupon_id = self.context['coupon_id']
        coupon = Coupon.objects.get(id=coupon_id)
        original_template = coupon.original_template

        # 1. 쿠폰이 완성된 쿠폰인지 확인합니다.
        if hasattr(coupon, 'stamps') and \
        (coupon.stamps.count() >= original_template.reward_info.amount):
            raise serializers.ValidationError("쿠폰이 이미 완성되었습니다.")

        # 2. 쿠폰의 유효기간이 경과하지 않았는지 확인합니다.
        if original_template.valid_until and original_template.valid_until < now():
            raise serializers.ValidationError("쿠폰의 유효기간이 지났습니다.")

        # 영수증 확인
        receipt = attrs.get("receipt")

        # 1. 영수증 번호가 등록되어 있는 영수증인지 확인합니다.
        if not receipt:
            raise serializers.ValidationError("DB에 등록되지 않은 영수증 번호입니다.")
        
        # 2. 영수증 번호에 해당하는 스탬프가 이미 등록되어 있는지 확인합니다.
        if hasattr(receipt, "stamp"):
            raise serializers.ValidationError("이미 스탬프가 발급된 영수증 번호입니다.")

        return super().validate(attrs)

    def create(self, validated_data) -> Stamp:
        """
        유효성 검증을 통과한 영수증 번호를 바탕으로 쿠폰 id와 유저를 바탕으로 스탬프 인스턴스를 생성하고 돌려줍니다.
        """
        receipt = validated_data.pop("receipt")
        coupon_id = self.context["coupon_id"]
        user = self.context["request"].user

        return Stamp.objects.create(receipt=receipt, coupon_id=coupon_id, customer=user)

    class Meta:
        model = Stamp
        fields = ["receipt"]

@extend_schema_serializer(
    examples=[
        OpenApiExample("예시", {"current_stamps": 1, "is_completed": False})
    ]
)
class StampCreateResponseSerializer(serializers.ModelSerializer):
    """
    스탬프 생성 후의 응답에 사용되는 시리얼라이저입니다.
    """

    current_stamps = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    
    def get_current_stamps(self, obj: Stamp) -> int:
        """
        스탬프 적립 후, 이 쿠폰의 스탬프 개수입니다.
        """
        coupon_id = self.context['coupon_id']
        return Coupon.objects.get(id=coupon_id).stamps.count()
    
    def get_is_completed(self, obj: Stamp) -> bool:
        """
        스탬프 적립 후, 이 쿠폰이 완성되었는지를 의미합니다.
        """
        return self.get_current_stamps(obj) >= obj.coupon.original_template.reward_info.amount
    
    class Meta:
        model = Stamp
        fields = ['current_stamps', 'is_completed']


# --------------------- 영수증 번호 입력 + 스탬프 발급 -> 없는 번호 등록 시 스탬프가 찍힐 가능성 우려 및 제거 -----------------
# class StampListRequestSerializer(serializers.ModelSerializer):
#     """
#     스탬프 생성(적립) 요청에 사용되는 시리얼라이저입니다.
#     `receipt_number` 필드로 영수증 번호를 받아 스탬프를 생성합니다.
#     """
#     receipt_number = serializers.CharField(write_only=True)

#     class Meta:
#         model = Stamp
#         fields = ["receipt_number"]

#     def validate(self, data):
#         """
#         1. 영수증 번호가 필요합니다.
#         2. 영수증 번호로 Receipt 객체를 조회하거나 새로 생성합니다.
#         3. 이미 스탬프가 발급된 영수증 번호인지 확인합니다.
#         """
#         num = data.get("receipt_number")
#         if not num:
#             raise serializers.ValidationError({"receipt_number": "영수증 번호가 필요합니다."})
#         # 정책 1: 없는 번호는 자동 생성
#         receipt, _ = Receipt.objects.get_or_create(receipt_number=num)
#         # 정책 2: 이미 사용된 영수증이면 거절
#         if hasattr(receipt, "stamp"):
#             raise serializers.ValidationError({"receipt_number": "이미 스탬프가 발급된 영수증 번호입니다."})
#         data["receipt"] = receipt
#         return data

#     def create(self, validated_data):
#         validated_data.pop("receipt_number", None)
#         receipt = validated_data.pop("receipt")
#         coupon_id = self.context["coupon_id"]
#         user = self.context["request"].user
#         return Stamp.objects.create(receipt=receipt, coupon_id=coupon_id, customer=user)

# ------------------------ 혜택 정보 ---------------------------
@extend_schema_serializer(
    examples=[
        OpenApiExample("예시", {"amount": 10, "reward": "아메리카노 1잔 무료"})
    ]
)
class RewardsInfoDetailResponseSerializer(serializers.ModelSerializer):
    """
    쿠폰에 해당하는 혜택 정보를 조회하는 시리얼라이저입니댜.
    """

    class Meta:
        model = RewardsInfo
        fields = ["amount", "reward"]

# ---------------------------- 가게 ---------------------------------------
@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "예시", 
            {
                "image_url": "(이미지 파일 URL)", 
                "name": "매머드 커피", 
                "lat": "37.21412582140", 
                "lng": "127.3432032904"
            }
        )
    ]
)
class PlaceListResponseSerializer(serializers.ModelSerializer):
    """
    List 계열의 시리얼라이저 내의 place 필드에 쓰여서 가게 정보를 간략하게 표시합니다.

    목록과 지도 겸용으로 설계되었습니다.
    """

    class Meta:
        model = Place
        fields = ['image_url', 'name', 'lat', 'lng']

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "예시",
            {
                "image_url": "(이미지 파일 URL)",
                "name": "매머드 커피",
                "address": "서울 동대문구 이문동 264-223",
                "opens_at": "08:00",
                "closes_at": "21:00",
                "last_order": "20:30",
                "tel": "0507-1361-0962",
                "lat": "37.21412582140",
                "lng": "127.3432032904",
            },
        )
    ]
)
class PlaceDetailResponseSerializer(PlaceListResponseSerializer):
    """
    Detail 계열의 시리얼라이저 내의 place 필드에 쓰여서 자세한 가게 정보를 표시합니다.
    """

    address = serializers.SerializerMethodField()
    opens_at = serializers.TimeField(TIME_FORMAT)
    closes_at = serializers.TimeField(TIME_FORMAT)
    last_order = serializers.TimeField(TIME_FORMAT)

    def get_address(self, obj: Place) -> str:
        """
        가게의 주소입니다.
        """
        legal_district = obj.address_district
        return f"{legal_district.province} {legal_district.city} {legal_district.district} " \
             f"{obj.address_rest}"

    class Meta(PlaceListResponseSerializer.Meta):
        fields =  [
            'image_url', 'name', 'address',
            'opens_at', 'closes_at', 'last_order', 'tel', 'lat', 'lng'
        ]

# ------------------------ 쿠폰 템플릿 -------------------------
@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "예시",
            {
                "id": 1,
                "coupon_template_url": "http://127.0.0.1/couponbook/coupon-templates/1/",
                "place": {
                    "image_url": "(이미지 파일 URL)",
                    "name": "매머드 커피",
                    "address": "서울 동대문구 이문동 264-223",
                    "opens_at": "08:00",
                    "closes_at": "21:00",
                    "last_order": "20:30",
                    "tel": "0507-1361-0962",
                    "lat": "37.21412582140",
                    "lng": "127.3432032904",
                },
                "reward_info": {
                    "amount": 10,
                    "reward": "아메리카노 1잔 무료"
                },
                "current_n_remaining": 30,
                "already_owned": True,
            },
        )
    ]
)
class CouponTemplateListSerializer(serializers.ModelSerializer):
    """
    점주가 등록하여 게시중인 쿠폰 템플릿을 조회하는 시리얼라이저입니다.
    """

    coupon_template_url = serializers.SerializerMethodField()
    place = PlaceDetailResponseSerializer()
    reward_info = RewardsInfoDetailResponseSerializer()
    current_n_remaining = serializers.SerializerMethodField()
    already_owned = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.URI)
    def get_coupon_template_url(self, obj: CouponTemplate):
        """
        해당 쿠폰 템플릿의 상세 조회 url입니다.
        """
        request = self.context['request']
        return reverse(
            'couponbook:coupon-template-detail', kwargs={'coupon_template_id': obj.id}, request=request
        )

    def get_current_n_remaining(self, obj: CouponTemplate) -> int | None:
        """
        현재 기준 남은 선착순 인원 수입니다.
        """
        if obj.first_n_persons and hasattr(obj, 'coupons'):
            return max(0, obj.first_n_persons - obj.coupons.count())
        elif obj.first_n_persons:
            return obj.first_n_persons
        else:
            return None

    def get_already_owned(self, obj: CouponTemplate) -> bool:
        """
        이미 해당 쿠폰 템플릿으로 생성한 쿠폰을 보유하고 있는지의 여부입니다.
        """
        if hasattr(obj, 'coupons'):
            return obj.coupons.filter(couponbook__user=self.context['request'].user).exists()
        
        return False # 이 쿠폰 템플릿으로 생성된 쿠폰이 없으므로 무조건 거짓일 수 밖에 없음
    
    class Meta:
        model = CouponTemplate
        fields = [
            'id', 'coupon_template_url', 'place', 'reward_info', 
            'current_n_remaining', 'already_owned'
        ]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "예시",
            {
                "id": 1,
                "place": {
                    "image_url": "(이미지 파일 URL)",
                    "name": "매머드 커피",
                    "address": "서울 동대문구 이문동 264-223",
                    "opens_at": "08:00",
                    "closes_at": "21:00",
                    "last_order": "20:30",
                    "tel": "0507-1361-0962",
                    "lat": "37.21412582140",
                    "lng": "127.3432032904",
                },
                "reward_info": {
                    "amount": 10,
                    "reward": "아메리카노 1잔 무료"
                },
                "current_n_remaining": 45,
                "already_owned": True,
            },
        )
    ]
)
class CouponTemplateDetailSerializer(CouponTemplateListSerializer):
    """
    개별 쿠폰 템플릿을 조회하는 응답에 사용되는 시리얼라이저입니다.
    """

    coupon_template_url = None # 개별 쿠폰 템플릿이므로 url 필요 없음
    place = PlaceDetailResponseSerializer()

    class Meta(CouponTemplateListSerializer.Meta):
        fields = [
            'id', 'place', 'reward_info', 'current_n_remaining', 'already_owned',
        ]


# 이 시리얼라이저는 프론트 쪽과 연결되어 사용되는 시리얼라이저는 아님
class CouponTemplateCreateSerializer(serializers.ModelSerializer):
    """
    점주가 새로운 쿠폰 템플릿을 등록할 때 사용하는 시리얼라이저입니다.
    `place` 필드는 뷰에서 현재 로그인된 점주와 연결된 가게 정보로 자동 할당됩니다.
    """

    reward_info = RewardsInfoDetailResponseSerializer(write_only=True, required=True)
    valid_until = serializers.DateTimeField(required=False, allow_null=True)

    class Meta:
        model = CouponTemplate
        # place 필드는 뷰에서 처리하므로 제외
        exclude = ["id", "place", "created_at"]

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
                "id": 1,
                "coupon_url": "http://127.0.0.1/couponbook/coupons/1/",
                "place": {
                    "image_url": "(이미지 파일 URL)",
                    "name": "매머드 커피",
                    "address": "서울 동대문구 이문동 264-223",
                    "opens_at": "08:00",
                    "closes_at": "21:00",
                    "last_order": "20:30",
                    "tel": "0507-1361-0962",
                    "lat": "37.21412582140",
                    "lng": "127.3432032904",
                },
                "reward_info": {
                    "amount": 10,
                    "reward": "아메리카노 1잔 무료"
                },
                "current_stamps": 7,
                "days_remaining": 10,
                "is_completed": False,
                "is_expired": False,
            }
        )
    ]
)
class CouponListResponseSerializer(serializers.ModelSerializer):
    """
    쿠폰의 목록을 조회하는 응답에 사용되는 시리얼라이저입니다.
    """

    coupon_url = serializers.SerializerMethodField()
    place = serializers.SerializerMethodField()
    reward_info = serializers.SerializerMethodField()
    current_stamps = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField() # 완료 여부 따라서 디자인이 바뀌는가..?
    is_expired = serializers.SerializerMethodField() # 만료 여부 따라서 디자인이 바뀌는가..?

    def get_coupon_reward_info(self, obj: Coupon) -> RewardsInfo | None:
        """
        해당 쿠폰에 연결된 리워드 정보를 가져옵니다.
        """

        if hasattr(obj, 'original_template') and hasattr(obj.original_template, 'reward_info'):
            return obj.original_template.reward_info
        
    def get_coupon_valid_until(self, obj: Coupon):
        """
        해당 쿠폰의 유효 기간을 가져옵니다. 유효 기간은 있을 수도 있고, None일 수도 있습니다.
        """

        if hasattr(obj, 'original_template') and hasattr(obj.original_template, 'valid_until'):
            return obj.original_template.valid_until

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
    
    # RewardsInfoDetailResponseSerializer | None으로 설정하면 spectacular warning 떠서 None 뺐음
    def get_reward_info(self, obj: Coupon) -> RewardsInfoDetailResponseSerializer:
        """
        해당 쿠폰의 리워드 정보입니다.
        """
        reward_info = self.get_coupon_reward_info(obj)

        if reward_info:
            return RewardsInfoDetailResponseSerializer(reward_info).data
        return None
    
    def get_current_stamps(self, obj: Coupon) -> int:
        """
        해당 쿠폰에 현재 적립되어 있는 스탬프 개수입니다.
        """
        stamps = Stamp.objects.filter(coupon=obj)
        return stamps.count()
    
    def get_days_remaining(self, obj: Coupon) -> int | None:
        """
        해당 쿠폰의 유효기간이 며칠 남아 있는지를 의미합니다.
        """
        valid_until = self.get_coupon_valid_until(obj)
        if not valid_until:
            return None
        return (valid_until - now()).days

    def get_is_completed(self, obj: Coupon) -> bool:
        """
        해당 쿠폰이 완성되었는지를 의미합니다.
        """
        reward_info = self.get_coupon_reward_info(obj)

        if reward_info:
            max_stamps: int = reward_info.amount
            current_stamps: int = Stamp.objects.filter(coupon=obj).count()

            return max_stamps == current_stamps
        return None

    def get_is_expired(self, obj: Coupon) -> bool:
        """
        해당 쿠폰의 유효기간이 만료되었는지를 의미합니다.
        """
        valid_until = obj.original_template.valid_until
        return bool(valid_until and valid_until < now())

    class Meta:
        model = Coupon
        fields = [
            'id', 'coupon_url', 'place', 'reward_info',
            'current_stamps', 'days_remaining',
            'is_completed', 'is_expired',
        ]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "단일 쿠폰 조회 응답 예시",
            {
                "is_favorite": True,
                "favorite_id": 1,
                "reward_info": {
                    "amount": 10,
                    "reward": "음료수 1잔 무료"
                },
                "current_stamps": 5,
                "place": {
                    "image_url": "(이미지 파일 URL)",
                    "name": "매머드 커피",
                    "address": "서울 동대문구 이문동 264-223",
                    "opens_at": "08:00",
                    "closes_at": "21:00",
                    "last_order": "20:30",
                    "tel": "0507-1361-0962",
                    "lat": "37.21412582140",
                    "lng": "127.3432032904",
                },
            },
        )
    ]
)
class CouponDetailResponseSerializer(CouponListResponseSerializer):
    """
    개별 쿠폰을 조회하는 응답에 사용되는 시리얼라이저입니다.
    """

    coupon_url = None # 이미 url을 알고 있으므로 필요 없음
    is_favorite = serializers.SerializerMethodField()
    favorite_id = serializers.SerializerMethodField()

    def get_coupon_owner_couponbook(self, obj: Coupon) -> CouponBook | None:
        """
        쿠폰 주인의 쿠폰북 인스턴스를 가져옵니다.

        특이한 경우 None이 반환될 수 있지만, 정상적인 상황에서는 쿠폰북 인스턴스가 반환되어야 합니다.
        """
        user = self.context["request"].user
        couponbook = CouponBook.objects.filter(user=user).first()
        
        return couponbook

    def get_is_favorite(self, obj: Coupon) -> bool:
        """
        해당 쿠폰을 즐겨찾기에 등록했는지의 여부입니다.
        """
        couponbook = self.get_coupon_owner_couponbook(obj)

        if hasattr(couponbook, 'favorite_coupons'):
            favorite_coupon = couponbook.favorite_coupons.filter(coupon=obj)

            return favorite_coupon.exists()
        return False # 쿠폰북의 즐겨찾기 쿠폰들이 없기 때문에 무조건 False일 수밖에 없음
    
    def get_favorite_id(self, obj: Coupon) -> int | None:
        """
        해당 쿠폰이 즐겨찾기에 등록되어 있을 때의 즐겨찾기 id입니다. 즐겨찾기 삭제에 사용합니다.
        """
        if self.get_is_favorite(obj):
            couponbook = self.get_coupon_owner_couponbook(obj)
            # get_is_favorite이 True가 반환되려면 favorite_coupons가 존재해야 하기 때문에 여기선 hasattr 사용하지 않아도 됨
            favorite_coupon_id = couponbook.favorite_coupons.get(coupon=obj).id

            return favorite_coupon_id
        return None
    
    class Meta(CouponListResponseSerializer.Meta):
        fields = [
            'id', 'is_favorite', 'favorite_id', 'reward_info',
            'current_stamps', 'place',
        ]

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "쿠폰 등록 요청",
            {
                "original_template": 1,
            },
        )
    ]
)
class CouponCreateRequestSerializer(serializers.ModelSerializer):
    """
    쿠폰을 생성하는 데에 사용되는 시리얼라이저입니다.
    `original_template` 필드로 쿠폰 템플릿 ID를 받습니다
    """

    def validate(self, attrs) -> dict:
        """
        1. 원본 쿠폰 템플릿이 존재하는지 확인합니다.
        2. 유효 기간이 만료되지 않았는지 확인합니다.
        3. 선착순 인원이 있다면 마감되지 않았는지 확인합니다.
        4. 이미 해당 유저가 해당 쿠폰 템플릿으로 등록한 쿠폰이 존재하는지 확인합니다.
        """

        # 1. 원본 쿠폰 템플릿이 존재하는지 확인합니다.
        original_template = attrs.get("original_template")
        if not original_template:
            raise serializers.ValidationError("해당 쿠폰 템플릿이 존재하지 않습니다.")
        
        # 2. 유효 기간이 만료되지 않았는지 확인합니다.
        if original_template.valid_until and original_template.valid_until < now():
            raise serializers.ValidationError("유효기간이 만료된 쿠폰 템플릿입니다.")
        
        # 3. 선착순 인원이 있다면 마감되지 않았는지 확인합니다.
        if hasattr(original_template, 'coupons') \
        and original_template.first_n_persons \
        and original_template.first_n_persons <= original_template.coupons.count():
            raise serializers.ValidationError("이미 선착순 마감된 쿠폰 템플릿입니다.")
        
        # 4. 이미 해당 유저가 해당 쿠폰 템플릿으로 등록한 쿠폰이 존재하는지 확인합니다.
        couponbook = self.context["couponbook"]
        coupon = Coupon.objects.filter(
            couponbook=couponbook, original_template=original_template
        )

        if coupon.exists():
            raise serializers.ValidationError(
                "이미 해당 쿠폰 템플릿으로 생성한 쿠폰이 존재합니다."
            )

        return super().validate(attrs)

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
            "즐겨찾기 목록 응답 예시",
            {
                "coupon": {
                    "id": 1,
                    "coupon_url": "http://127.0.0.1/couponbook/coupons/1/",
                    "place": {
                        "image_url": "(이미지 파일 URL)",
                        "name": "매머드 커피",
                        "address": "서울 동대문구 이문동 264-223",
                        "opens_at": "08:00",
                        "closes_at": "21:00",
                        "last_order": "20:30",
                        "tel": "0507-1361-0962",
                        "lat": "37.21412582140",
                        "lng": "127.3432032904",
                    },
                    "reward_info": {
                        "amount": 10,
                        "reward": "아메리카노 1잔 무료"
                    },
                    "current_stamps": 7,
                    "days_remaining": 10,
                    "is_completed": False,
                    "is_expired": False,
                }
            }
        )
    ]
)
class FavoriteCouponListResponseSerializer(serializers.ModelSerializer):
    """
    즐겨찾기 등록한 쿠폰을 조회하는 응답에 사용되는 시리얼라이저입니다.
    """

    coupon = CouponListResponseSerializer()

    class Meta:
        model = FavoriteCoupon
        fields = ['coupon']

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "즐겨찾기 등록 요청",
            {
                "coupon": 1,
            },
        )
    ]
)
class FavoriteCouponCreateRequestSerializer(serializers.ModelSerializer):
    """
    쿠폰을 즐겨찾기를 등록할 때 사용되는 시리얼라이저입니다.
    """

    def validate(self, attrs) -> dict:
        """
        1. 해당 쿠폰 id에 해당하는 쿠폰이 존재하는지 확인합니다.
        2. 해당 쿠폰북에 해당 쿠폰이 즐겨찾기로 등록되어 있는지 확인합니다.
        """
        coupon = attrs.get("coupon")

        if not coupon:
            raise serializers.ValidationError(
                "쿠폰 id에 해당하는 쿠폰이 존재하지 않습니다."
            )

        couponbook = self.context["couponbook"]
        favorite_coupon = couponbook.favorite_coupons.filter(coupon=coupon)

        if favorite_coupon.exists():
            raise serializers.ValidationError("이미 즐겨찾기 등록된 쿠폰입니다.")

        return super().validate(attrs)

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
            "즐겨찾기 상세 응답 예시",
            {
                "id": 1,
                "added_at": "2025-08-18 21:40",
                "coupon": 1,
            },
        )
    ]
)
class FavoriteCouponCreateResponseSerializer(serializers.ModelSerializer):
    """
    즐겨찾기 쿠폰을 등록했을 때의 응답에 사용되는 시리얼라이저입니다.
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
class CouponBookDetailResponseSerializer(serializers.ModelSerializer):
    """
    쿠폰북을 조회하는 응답에 사용되는 시리얼라이저입니다.
    """

    favorite_counts = serializers.SerializerMethodField()
    coupon_counts = serializers.SerializerMethodField()
    stamp_counts = serializers.SerializerMethodField()

    def get_favorite_counts(self, obj: CouponBook) -> int:
        """
        즐겨찾기한 쿠폰의 개수입니다.
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


# ----------------- account 앱에서 쓰는 가게 시리얼라이저 ---------------------
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
