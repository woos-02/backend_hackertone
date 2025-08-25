import django_filters as filters
from django.db.models import CharField, Q, Value
from django.db.models.functions import Concat
from django.utils import timezone

from .models import Coupon, CouponTemplate


def get_queryset_with_full_addr(queryset, field_name: str=""):
    """
    모델 네임을 prefix로 사용하여 주소 annotation이 포함된 쿼리셋을 반환합니다.
    """
    prefix = f'{field_name}__' if field_name else ''

    return queryset.annotate(
        full_addr=Concat(
            prefix+'place__address_district__province',
            Value(' '),
            prefix+'place__address_district__city',
            Value(' '),
            prefix+'place__address_district__district',
            Value(' '),
            prefix+'place__address_rest',
            output_field=CharField(),
        )
    )

class CouponFilter(filters.FilterSet):
    """
    쿠폰 목록 필터 (쿠폰북 내 쿠폰 조회용)
    - address : '광역시 시/군/구 법정동 + 상세주소(address_rest)' 풀 문자열 부분검색
    - district: 법정동 명(예: 이문동) 정확 매칭(대소문자 무시)
    - name    : 가게명 부분검색
    - is_open : 현재 영업중 여부
    - is_expired : 템플릿 유효기간 만료 여부
    """

    address = filters.CharFilter(method="filter_address")
    district = filters.CharFilter(
        field_name="original_template__place__address_district__district",
        lookup_expr="iexact",
    )
    name = filters.CharFilter(
        field_name="original_template__place__name", lookup_expr="icontains"
    )
    is_open = filters.BooleanFilter(method="filter_is_open")
    is_expired = filters.BooleanFilter(method="filter_is_expired")

    def filter_address(self, queryset, name: str, value: str):
        """
        가게의 광역시 ~ 법정동 주소를 기준으로 필터링합니다. (부분 일치)
        """
        
        if not value:
            return queryset
        q = get_queryset_with_full_addr(queryset, 'original_template')
        return q.filter(full_addr__icontains=value)

    def filter_is_open(self, queryset, name: str, value: bool):
        """
        가게의 현재 영업 중 여부를 바탕으로 필터링합니다.
        """

        if value is None:
            return queryset
        now = timezone.localtime().time()
        cond = (
            Q(original_template__place__opens_at__lte=now)
            & Q(original_template__place__last_order__gt=now)
        )
        return queryset.filter(cond) if value else queryset

    def filter_is_expired(self, queryset, name: str, value: bool):
        """
        true라면 만료된 쿠폰만 조회하고, 그렇지 않다면 모든 쿠폰을 조회합니다.
        """

        if value is None:
            return queryset
        now_dt = timezone.now()
        expired = Q(original_template__valid_until__isnull=False) & Q(
            original_template__valid_until__lt=now_dt
        )
        return queryset.filter(expired) if value else queryset
    
    class Meta:
        model = Coupon
        fields = ["address", "district", "name", "is_open", "is_expired"]

class CouponTemplateFilter(filters.FilterSet):
    """
    템플릿 목록 필터 (/couponbook/coupon-templates/)
    - address    : '광역시 시/군/구 법정동 + 상세주소' 부분검색
    - district   : 법정동 명 정확 매칭(대소문자 무시)
    - name       : 가게명 부분검색
    - tag        : 가게 태그 부분검색
    - is_open    : 현재 영업중 여부
    - already_own: (로그인시) 내가 이미 보유한/보유하지 않은 템플릿
    """

    name = filters.CharFilter(field_name="place__name", lookup_expr="icontains")
    tag = filters.CharFilter(field_name="place__tags", lookup_expr="icontains")
    district = filters.CharFilter(
        field_name="place__address_district__district", lookup_expr="iexact"
    )
    address = filters.CharFilter(method="filter_address")
    is_open = filters.BooleanFilter(method="filter_is_open")
    already_own = filters.BooleanFilter(method="filter_already_own")

    def filter_address(self, queryset, name: str, value: str):
        """
        가게의 광역시 ~ 법정동 주소를 기준으로 필터링합니다. (부분 일치)
        """
        
        if not value:
            return queryset
        q = get_queryset_with_full_addr(queryset)
        return q.filter(full_addr__icontains=value)

    def filter_is_open(self, queryset, name: str, value: bool):
        """
        가게의 현재 영업 중 여부를 바탕으로 필터링합니다.
        """
        
        if value is None:
            return queryset
        now = timezone.localtime().time()
        cond = Q(place__opens_at__lte=now) & Q(place__last_order__gt=now)
        return queryset.filter(cond) if value else queryset

    def filter_already_own(self, queryset, name: str, value: bool):
        """
        true라면 이미 보유한 쿠폰 템플릿만 보여주고, 그렇지 않다면 모든 쿠폰 템플릿을 보여줍니다.
        """
        
        # 미입력 시 필터 미적용
        if value is None:
            return queryset

        user = getattr(self.request, "user", None)
        # 비로그인 사용자가 already_own을 True로 요청하면 결과 없음, False면 전체 반환
        if not user or not user.is_authenticated:
            return queryset.none() if value else queryset

        # Coupon.couponbook(user) -> Coupon.original_template(=CouponTemplate) 경로
        owned_qs = queryset.filter(coupons__couponbook__user=user).distinct()
        return owned_qs if value else queryset
    
    class Meta:
        model = CouponTemplate
        fields = ["name", "tag", "district", "address", "is_open", "already_own"]
