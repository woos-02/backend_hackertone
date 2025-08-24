# AI 큐레이터에서 사용하기 위한 데이터 시리얼라이저

from couponbook.models import CouponBook, Place
from couponbook.serializers import CouponTemplateListSerializer
from rest_framework import serializers


class PlaceWithoutPersonalInfoSerializer(serializers.ModelSerializer):
    """
    전화번호, 상세 주소와 같은 개인정보를 제거하고 AI에게 전달하기 위한 시리얼라이저입니다.
    """
    image_url = None # 이미지 url 필요없음
    address= serializers.SerializerMethodField()

    def get_address(self, obj: Place):
        return f"{obj.address_district.province} {obj.address_district.city} {obj.address_district.district}"

    class Meta:
        model = Place
        fields = ['name', 'address']

class CouponTemplateDictSerializer(CouponTemplateListSerializer):
    """
    위도, 경도, url과 같은 불필요한 정보를 제거하고 AI에게 전달하기 위한 시리얼라이저입니다.
    """

    coupon_template_url = None # AI에 서버 정보 전달하지 않음
    place = PlaceWithoutPersonalInfoSerializer()
    already_owned = None # 기보유 정보 제거

    class Meta(CouponTemplateListSerializer.Meta):
        fields = ['id', 'place', 'reward_info', 'current_n_remaining']
