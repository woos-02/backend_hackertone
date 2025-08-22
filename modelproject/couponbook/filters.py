import django_filters as filters
from django.db.models import Q, Value, CharField
from django.db.models.functions import Concat
from django.utils import timezone

from .models import Coupon, CouponTemplate


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

    def filter_already_own(self, queryset, name, value):
        """
        이미 보유한 쿠폰인지 필터링하는 메소드입니다.
        """
        if value:
            return queryset.filter(coupons__couponbook__user=self.request.user)
        return queryset
    
    def filter_is_open(self, queryset, name, value):
        if value:
            return queryset.filter(place__opens_at__lte=datetime.now().time(),
                                   place__closes_at__gte=datetime.now().time())
        return queryset
    
    class Meta:
        model = Coupon
        fields = ["address", "district", "name", "is_open", "is_expired"]

    def filter_address(self, queryset, name: str, value: str):
        if not value:
            return queryset
        q = queryset.annotate(
            full_addr=Concat(
                "original_template__place__address_district__province",
                Value(" "),
                "original_template__place__address_district__city",
                Value(" "),
                "original_template__place__address_district__district",
                Value(" "),
                "original_template__place__address_rest",
                output_field=CharField(),
            )
        )
        return q.filter(full_addr__icontains=value)

    def filter_is_open(self, queryset, name: str, value: bool):
        if value is None:
            return queryset
        now = timezone.localtime().time()
        cond = (
            Q(original_template__place__opens_at__lte=now)
            & Q(original_template__place__last_order__gt=now)
        )
        return queryset.filter(cond) if value else queryset

    def filter_is_expired(self, queryset, name: str, value: bool):
        if value is None:
            return queryset
        now_dt = timezone.now()
        expired = Q(original_template__valid_until__isnull=False) & Q(
            original_template__valid_until__lt=now_dt
        )
        return queryset.filter(expired) if value else queryset


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

    class Meta:
        model = CouponTemplate
        fields = ["name", "tag", "district", "address", "is_open", "already_own"]

    def filter_address(self, queryset, name: str, value: str):
        if not value:
            return queryset
        q = queryset.annotate(
            full_addr=Concat(
                "place__address_district__province",
                Value(" "),
                "place__address_district__city",
                Value(" "),
                "place__address_district__district",
                Value(" "),
                "place__address_rest",
                output_field=CharField(),
            )
        )
        return q.filter(full_addr__icontains=value)

    def filter_is_open(self, queryset, name: str, value: bool):
        if value is None:
            return queryset
        now = timezone.localtime().time()
        cond = Q(place__opens_at__lte=now) & Q(place__last_order__gt=now)
        return queryset.filter(cond) if value else queryset

    def filter_already_own(self, queryset, name: str, value: bool):
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

# from datetime import datetime

# from django.db.models import CharField
# from django.db.models import Value as V
# from django.db.models.functions import Concat
# from django.utils.timezone import now
# from django_filters import rest_framework as filters

# from .models import Coupon, CouponTemplate


# class CouponTemplateFilter(filters.FilterSet):
#     """
#     쿠폰 템플릿을 필터링하는 필터셋입니다.
#     """
#     name = filters.CharFilter(field_name='place__name', 
#                               lookup_expr='icontains',
#                               help_text="가게 이름입니다. (영어의 경우 대소문자 구분 없음)")
#     address = filters.CharFilter(field_name='place__address_district',
#                                  method='filter_address',
#                                  help_text="가게의 광역시 ~ 법정동 주소입니다. 일부 일치 검색입니다.")
#     district = filters.CharFilter(field_name='place__address_district__district',
#                                   help_text="가게의 법정동 주소 중 법정동 부분입니다. 정확하게 일치해야 합니다.")
#     already_own = filters.BooleanFilter(field_name='couponbook__user',
#                                         method='filter_already_own',
#                                         help_text="이미 쿠폰북에 해당 쿠폰 템플릿으로 등록된 쿠폰이 있는지 여부입니다.")
#     is_open = filters.BooleanFilter(field_name='place',
#                                     method='filter_is_open',
#                                     help_text="현재 영업중인지 여부입니다.")
#     tag = filters.CharFilter(field_name='place__tags',
#                              lookup_expr='icontains',
#                              help_text="가게의 태그입니다. 한 태그씩만 검색할 수 있습니다.")


#     def filter_address(self, queryset, name, value):
#         """
#         광역시 ~ 법정동을 기준으로 필터링하는 메소드입니다.
#         """
#         q = queryset.annotate(
#             address_district=Concat(
#                 f'{name}__province', V(' '),
#                 f'{name}__city', V(' '), 
#                 f'{name}__district',
#                 output_field=CharField()))
#         return q.filter(address_district__icontains=value)

#     def filter_already_own(self, queryset, name, value):
#         """
#         이미 보유한 쿠폰인지 필터링하는 메소드입니다.
#         """
#         if value:
#             return queryset.filter(coupons__couponbook__user=self.request.user)
#         return queryset
    
#     def filter_is_open(self, queryset, name, value):
#         if value:
#             return queryset.filter(place__opens_at__lte=datetime.now().time(),
#                                    place__closes_at__gte=datetime.now().time())
#         return queryset
    
#     class Meta:
#         model = CouponTemplate
#         fields = []

# class CouponFilter(filters.FilterSet):
#     """
#     보유하고 있는 쿠폰을 필터링하는 필터셋입니다.
#     """
#     field_prefix = 'original_template__'
#     name = filters.CharFilter(field_name=field_prefix+'place__name',
#                               lookup_expr='icontains',
#                               help_text="가게 이름입니다. (영어의 경우 대소문자 구분 없음)")
#     address = filters.CharFilter(field_name=field_prefix+'place__address_district',
#                                  method='filter_address',
#                                  help_text="가게의 광역시 ~ 법정동 주소입니다. 일부 일치 검색입니다.")
#     district = filters.CharFilter(field_name=field_prefix+'place__address_district__district',
#                                   help_text="가게의 법정동 주소 중 법정동 부분입니다. 정확하게 일치해야 합니다.")
#     is_expired = filters.BooleanFilter(field_name=field_prefix+'valid_until',
#                                        method='filter_is_expired',
#                                        help_text="만료된 쿠폰인지를 의미합니다. true 또는 false입니다.")
#     is_open = filters.BooleanFilter(field_name=field_prefix+'place',
#                                     method='filter_is_open',
#                                     help_text="현재 영업중인지 여부입니다.")
#     tag = filters.CharFilter(field_name=field_prefix+'place__tags',
#                              lookup_expr='icontains',
#                              help_text="가게의 태그입니다. 한 태그씩만 검색할 수 있습니다.")
    

#     def filter_address(self, queryset, name, value):
#         """
#         광역시 ~ 법정동을 기준으로 필터링하는 메소드입니다.
#         """
#         q = queryset.annotate(
#             address_district=Concat(
#                 f'{name}__province', V(' '),
#                 f'{name}__city', V(' '), 
#                 f'{name}__district',
#                 output_field=CharField()))
#         return q.filter(address_district__icontains=value)
    
#     def filter_is_expired(self, queryset, name, value):
#         if value:
#             return queryset.filter(original_template__valid_until__lt=now())
#         return queryset
    
#     def filter_is_open(self, queryset, name, value):
#         if value:
#             return queryset.filter(original_template__place__opens_at__lte=datetime.now().time(),
#                                    original_template__place__closes_at__gte=datetime.now().time())
#         return queryset
    
#     class Meta:
#         model = Coupon
#         fields = []