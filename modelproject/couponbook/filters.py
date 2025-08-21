from django.db.models import CharField
from django.db.models import Value as V
from django.db.models.functions import Concat
from django_filters import rest_framework as filters

from .models import Coupon, CouponTemplate


class CouponTemplateFilter(filters.FilterSet):
    """
    쿠폰 템플릿을 필터링하는 필터셋입니다.
    """
    name = filters.CharFilter(field_name='place__name', 
                              lookup_expr='icontains',
                              help_text="가게 이름입니다. (영어의 경우 대소문자 구분 없음)")
    address = filters.CharFilter(field_name='place__address_district',
                                 method='filter_address',
                                 help_text="가게의 광역시 ~ 법정동 주소입니다. 일부 일치 검색입니다.")
    district = filters.CharFilter(field_name='place__address_district__district',
                                  help_text="가게의 법정동 주소 중 법정동 부분입니다. 정확하게 일치해야 합니다.")
    # todo: 보유 여부에 따른 필터링 추가 + 태그 필터링 추가

    def filter_address(self, queryset, name, value):
        """
        광역시 ~ 법정동을 기준으로 필터링하는 메소드입니다.
        """
        q = queryset.annotate(
            address_district=Concat(
                f'{name}__province', V(' '),
                f'{name}__city', V(' '), 
                f'{name}__district',
                output_field=CharField()))
        return q.filter(address_district__icontains=value)

    class Meta:
        model = CouponTemplate
        fields = []

class CouponFilter(filters.FilterSet):
    """
    보유하고 있는 쿠폰을 필터링하는 필터셋입니다.
    """
    field_prefix = 'original_template__'
    name = filters.CharFilter(field_name=field_prefix+'place__name',
                              lookup_expr='icontains',
                              help_text="가게 이름입니다. (영어의 경우 대소문자 구분 없음)")
    address = filters.CharFilter(field_name=field_prefix+'place__address_district',
                                 method='filter_address',
                                 help_text="가게의 광역시 ~ 법정동 주소입니다. 일부 일치 검색입니다.")
    district = filters.CharFilter(field_name=field_prefix+'place__address_district__district',
                                  help_text="가게의 법정동 주소 중 법정동 부분입니다. 정확하게 일치해야 합니다.")
    # todo: 태그 필터링 추가
    
    def filter_address(self, queryset, name, value):
        """
        광역시 ~ 법정동을 기준으로 필터링하는 메소드입니다.
        """
        q = queryset.annotate(
            address_district=Concat(
                f'{name}__province', V(' '),
                f'{name}__city', V(' '), 
                f'{name}__district',
                output_field=CharField()))
        return q.filter(address_district__icontains=value)
    
    class Meta:
        model = Coupon
        fields = []
