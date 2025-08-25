from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema, extend_schema_view)
from rest_framework import filters, permissions
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import (CreateAPIView, DestroyAPIView,
                                     ListAPIView, ListCreateAPIView,
                                     RetrieveAPIView, RetrieveDestroyAPIView)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from .curation.utils import AICurator, UserStatistics
from .filters import CouponFilter, CouponTemplateFilter
from .models import *
from .models import CouponTemplate
from .permissions import IsMyCoupon, IsMyCouponBook, IsMyCouponForFavoriteAdd
from .serializers import *

# Create your views here.

# 각 인스턴스를 얻는 로직은 아래와 같습니다.
# 1. 개별 쿠폰북을 현재 로그인된 user의 id를 바탕으로 얻습니다.
#     - 돌아오는 응답에 쿠폰북의 id가 포함되어 있습니다.
# 2. 쿠폰의 목록을 쿠폰북의 id를 바탕으로 얻습니다.
#     - 돌아오는 응답에 개별 쿠폰의 id가 포함되어 있습니다.
# 3. 개별 쿠폰을 쿠폰의 id를 통해 얻습니다.
# 4. 스탬프의 목록을 쿠폰의 id를 바탕으로 얻습니다.
#     - 돌아오는 응답에 개별 스탬프의 id가 포함되어 있습니다.
# 5. 개별 스탬프를 스탬프의 id를 통해 얻습니다.

# 각 뷰에는 공통 속성을 먼저 작성하고, 한 줄 공백을 두고 개별 속성 및 메소드를 작성했습니다.
# 공통 속성: serializer_class, authentication_classes, permission_classes


# --------------------------------------- 쿠폰북 ---------------------------------------------
@extend_schema_view(
    get=extend_schema(
        tags=["CouponBook"],
        description="현재 로그인된 유저의 유저 id(username이 아닙니다)에 해당하는 쿠폰북을 조회합니다.",
        summary="현재 로그인된 유저의 쿠폰북 조회",
        responses=CouponBookDetailResponseSerializer,
    )
)
class CouponBookDetailView(RetrieveAPIView):
    """
    한 쿠폰북을 조회하는 뷰입니다. 로그인된 유저의 유저 id에 해당하는 쿠폰북을 조회합니다.
    """

    serializer_class = CouponBookDetailResponseSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated] # get_object에서 본인의 쿠폰북을 가져오기 때문에 IsAuthenticated 사용

    queryset= CouponBook.objects.all()

    def get_object(self):
        """
        로그인된 유저의 유저 id에 해당하는 쿠폰북 인스턴스를 가져옵니다.
        """
        queryset = self.filter_queryset(self.get_queryset())
        # 로그인된 유저의 유저 id에 해당하는 쿠폰북이 없으면 404가 발생합니다.
        # 유저의 회원가입 시기에 쿠폰북이 자동 생성되므로, 이 예외는 일반적으로 발생하면 안됩니다.
        obj = get_object_or_404(queryset, user=self.request.user)
        return obj


# ----------------------------- 쿠폰 ---------------------------------------
@extend_schema_view(
    get=extend_schema(
        tags=["Coupons"],
        description="쿠폰북 id에 해당하는 쿠폰북에 속한 쿠폰들의 목록을 가져옵니다.",
        summary="쿠폰북에 속한 쿠폰들의 목록 조회",
        parameters=[
            OpenApiParameter('couponbook_id', int, OpenApiParameter.PATH),
            OpenApiParameter('address', str, OpenApiParameter.QUERY,
                             description='가게의 광역시 ~ 법정동 주소입니다. 일부 일치 검색입니다.'),
            OpenApiParameter('district', str, OpenApiParameter.QUERY,
                             description='가게의 법정동 주소 중 법정동 부분입니다. 정확하게 일치해야 합니다.'),
            OpenApiParameter('name', str, OpenApiParameter.QUERY,
                             description='가게 이름입니다. (영어의 경우 대소문자 구분 없음)'),
            OpenApiParameter('is_expired', bool, OpenApiParameter.QUERY,
                             description='쿠폰의 만료 여부입니다. (true / false, 대소문자 구별 없음)'),
            OpenApiParameter('is_open', bool, OpenApiParameter.QUERY,
                             description='현재 영업중인지 여부입니다. (true / false, 대소문자 구별 없음)'),
            OpenApiParameter('ordering', str, OpenApiParameter.QUERY,
                             description='정렬 기준입니다. stamp_counts: 스탬프 개수 오름차순 / -stamp_counts: 스탬프 개수 내림차순'),
        ]
    ),
    post=extend_schema(
        tags=["Coupons"],
        description="쿠폰북 id에 해당하는 쿠폰북에 쿠폰 템플릿 id에 해당하는 쿠폰 템플릿 정보를 바탕으로 실사용 쿠폰을 생성하여 등록합니다.",
        summary="쿠폰 템플릿 바탕으로 실사용 쿠폰 등록",
        request=CouponCreateRequestSerializer,
        responses=CouponDetailResponseSerializer,
        examples=[OpenApiExample("요청 예시", value={"original_template": 1}, request_only=True)],
    ),
)
class CouponListView(ListCreateAPIView):
    """
    쿠폰 목록에 관련된 뷰입니다. 쿠폰북에 속한 쿠폰들의 목록을 가져옵니다.
    """

    serializer_class = CouponListResponseSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMyCouponBook]
    queryset = Coupon.objects.none() # drf-spectacular warning 방지
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = CouponFilter
    ordering_fields = ['id', 'saved_at', 'stamp_counts']

    def get_queryset(self):
        """
        URL의 couponbook_id를 바탕으로 해당 쿠폰북에 속한 쿠폰들을 조회합니다.
        """

        couponbook_id: int = self.kwargs['couponbook_id']
        queryset = Coupon.objects.filter(couponbook_id=couponbook_id)
        queryset = queryset.annotate(stamp_counts=Count('stamps'))

        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CouponListResponseSerializer
        return CouponCreateRequestSerializer
    
    def create(self, request, *args, **kwargs):
        """
        쿠폰 템플릿 id를 받아서, 해당 쿠폰 템플릿을 바탕으로 실사용 쿠폰을 생성합니다.
        """

        couponbook_id = self.kwargs['couponbook_id']
        couponbook = get_object_or_404(CouponBook, id=couponbook_id)
        request_serializer = self.get_serializer_class()(data=request.data, context={'request': request, 'couponbook': couponbook})
        request_serializer.is_valid(raise_exception=True)
        instance = self.perform_create(request_serializer)
        response_serializer = CouponDetailResponseSerializer(instance, context={'request': request, 'couponbook': couponbook})
        headers = self.get_success_headers(request_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer) -> Coupon:
        """
        시리얼라이저에 의해 저장된 데이터를 반환하도록 하여 응답용 시리얼라이저에 인스턴스를 넣을 수 있게 합니다.
        """

        return serializer.save()

@extend_schema_view(
    get=extend_schema(
        tags=["Coupons"],
        description="쿠폰 id에 해당하는 쿠폰을 조회합니다. " \
            "쿠폰 목록 조회와는 다르게 쿠폰 id를 path parmaeter로 취하는 점에 주의해야 합니다.",
        summary="단일 쿠폰 조회",
        responses=CouponDetailResponseSerializer,
    )
)
class CouponDetailView(RetrieveDestroyAPIView):
    """
    한 쿠폰에 관련된 뷰입니다. 쿠폰 id에 해당하는 쿠폰을 조회하거나 삭제합니다.
    """

    serializer_class = CouponDetailResponseSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMyCoupon]

    queryset = Coupon.objects.all()
    lookup_url_kwarg = 'coupon_id'

@extend_schema_view(
    get=extend_schema(
        tags=["AI_CURATION"],
        description="현재 유저가 보유한 쿠폰을 바탕으로 쿠폰 큐레이션을 실행하여 추천된 쿠폰들의 목록을 반환합니다.",
        summary="AI 기반 추천 쿠폰 목록 반환",
    )
)
class CouponTemplateCurationView(ListAPIView):
    """
    쿠폰 템플릿 추천과 관련된 뷰입니다.
    """

    serializer_class = CouponTemplateListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):# -> Any:
        """
        현재 유저의 쿠폰 컬렉션을 바탕으로 쿠폰 템플릿 큐레이션을 실행하여 추천된 쿠폰 템플릿들의 쿼리셋을 반환합니다.
        """

        user_statistics = UserStatistics(self.request.user)

        # 유효 기간 지난 것 제거, 현재 게시중인 것만 보이게 하고, 이미 보유한 쿠폰 템플릿 제거
        coupon_templates = CouponTemplate.objects.filter(
            Q(valid_until=None) | Q(valid_until__gte=now()), is_on=True).exclude(coupons__couponbook__user=self.request.user)

        curator = AICurator()
        coupon_templates_ids = curator.curate(user_statistics, coupon_templates)
        return CouponTemplate.objects.filter(id__in=coupon_templates_ids)
    
@extend_schema_view(
    get=extend_schema(
        tags=["Favorites"],
        description="현재 로그인되어 있는 유저의 쿠폰북에 등록되어 있는 즐겨찾기 쿠폰들을 조회합니다.",
        summary="즐겨찾기 쿠폰 목록 조회",
        responses=FavoriteCouponListResponseSerializer,
    ),
    post=extend_schema(
        tags=["Favorites"],
        description="현재 로그인되어 있는 유저의 쿠폰북에 쿠폰 id에 해당하는 쿠폰을 즐겨찾기에 등록합니다.",
        summary="즐겨찾기 쿠폰 등록",
        request=FavoriteCouponCreateRequestSerializer,
        responses=FavoriteCouponCreateResponseSerializer,
        examples=[
            OpenApiExample("요청 예시", value={"coupon": 1}, request_only=True)
        ],
    )
)
class FavoriteCouponListView(ListCreateAPIView):
    """
    현재 쿠폰북에 등록되어 있는 즐겨찾기 쿠폰들을 조회하는 뷰입니다.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMyCouponBook, IsMyCouponForFavoriteAdd]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return FavoriteCouponListResponseSerializer
        return FavoriteCouponCreateRequestSerializer

    def get_queryset(self):
        """
        현재 쿠폰북의 couponbook_id를 바탕으로 해당 쿠폰북에 속한 즐겨찾기 쿠폰들을 조회합니다.
        """

        couponbook_id = self.kwargs['couponbook_id']
        queryset = FavoriteCoupon.objects.filter(couponbook_id=couponbook_id)
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        coupon_id를 받아서, coupon_id에 해당하는 쿠폰을 현재 쿠폰북에 즐겨찾기 쿠폰으로 등록합니다.
        """

        couponbook_id = self.kwargs['couponbook_id']
        couponbook = get_object_or_404(CouponBook, id=couponbook_id)
        request_serializer = self.get_serializer_class()(data=request.data, context={'request': request, 'couponbook': couponbook})
        request_serializer.is_valid(raise_exception=True)
        instance = self.perform_create(request_serializer)
        headers = self.get_success_headers(request_serializer.data)
        response_serializer = FavoriteCouponCreateResponseSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer) -> FavoriteCoupon:
        """
        시리얼라이저에 의해 저장된 데이터를 반환하도록 하여 응답용 시리얼라이저에 인스턴스를 넣을 수 있게 합니다.
        """
        return serializer.save()

@extend_schema_view(
    delete=extend_schema(
        tags=["Favorites"],
        description="즐겨찾기 쿠폰 id에 해당하는 쿠폰을 즐겨찾기 목록에서 제거합니다.",
        summary="즐겨찾기 쿠폰 제거",
        responses={204: {"description": "성공적으로 삭제됨 (No Content)"}},
    )
)
class FavoriteCouponDetailView(DestroyAPIView):
    """
    현재 즐겨찾기 쿠폰을 즐겨찾기에서 삭제하는 뷰입니다.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = FavoriteCoupon.objects.all()
    lookup_url_kwarg = 'favorite_id'


from drf_spectacular.utils import extend_schema, extend_schema_view
# ----------------------------- 쿠폰 템플릿 (통합) -------------------------------
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError


@extend_schema_view(
    get=extend_schema(
        tags=["Templates"],
        summary="현재 게시중인 쿠폰 템플릿 목록 조회",
        description="현재 게시중('is_on')으로 설정된 쿠폰 템플릿들의 목록을 가져옵니다.",
        responses=CouponTemplateListSerializer,
        auth=None,
    ),
    post=extend_schema(
        tags=["Templates"],
        summary="점주: 새로운 쿠폰 템플릿 등록",
        description="(OWNER 전용) 로그인 필요. 본인 place에 템플릿을 등록합니다.",
        request=CouponTemplateCreateSerializer,
        responses={201: CouponTemplateCreateSerializer},
    ),
)
class CouponTemplateListView(ListCreateAPIView):
    """
    쿠폰 템플릿 목록 조회(GET) + 템플릿 생성(POST, 점주 전용)
    """

    authentication_classes = [JWTAuthentication]
    queryset = CouponTemplate.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = CouponTemplateFilter

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CouponTemplateListSerializer
        return CouponTemplateCreateSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        # 점주 검증
        if not getattr(user, "is_owner", lambda: False)():
            raise PermissionDenied("점주만 쿠폰 템플릿을 등록할 수 있습니다.")
        # 가게 보유 검증
        place = getattr(user, "place", None)
        if place is None:
            raise ValidationError({"detail": "등록된 가게가 없습니다. 먼저 가게를 등록해주세요."})
        serializer.save(place=place)
        
    def get_queryset(self):
        """
        FK(Place -> LegalDistrict)를 직렬화에서 접근하므로
        select_related로 한 번에 조인해 안전/성능을 확보합니다.
        """

        # 부모에 get_queryset이 있으면 사용, 없으면 기본 queryset 사용
        qs = super().get_queryset() if hasattr(super(), "get_queryset") else self.queryset
        # Place 및 LegalDistrict 조인 + 추가 필터링
        return qs.select_related("place", "place__address_district").filter(Q(valid_until=None) | Q(valid_until__gte=now()), is_on=True)

@extend_schema_view(
    get=extend_schema(
        tags=["Templates"],
        description="현재 게시중으로 설정된 쿠폰 템플릿들 중 쿠폰 템플릿 id에 해당하는 쿠폰 템플릿을 가져옵니다.",
        summary="현재 게시중인 단일 쿠폰 템플릿 조회",
        responses=CouponTemplateDetailSerializer,
    )
)
class CouponTemplateDetailView(RetrieveAPIView):
    """
    한 쿠폰 템플릿을 조회하는 뷰입니다.
    """

    serializer_class = CouponTemplateDetailSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    # 유효기간이 경과되지 않은 현재 게시중으로 설정된 쿠폰 템플릿 조회
    queryset = CouponTemplate.objects.filter(Q(valid_until=None) | Q(valid_until__gte=now()), is_on=True)
    lookup_url_kwarg = 'coupon_template_id'


# -------------------------------- 스탬프 ---------------------------------
@extend_schema_view(
    post=extend_schema(
        tags=["Stamps"],
        description="영수증 번호를 바탕으로 영수증이 존재하는지, 스탬프가 이미 등록되지 않았는지 확인하고, 두 조건 모두 만족하면 스탬프를 등록합니다.",
        summary="영수증 번호를 바탕으로 스탬프 등록",
        request=StampCreateRequestSerializer,
        responses=StampCreateResponseSerializer,
        examples=[OpenApiExample("요청 예시", value={"receipt": "00000001"}, request_only=True)],
    )
)
class StampListView(CreateAPIView):
    """
    스탬프 적립(등록)과 관련된 뷰입니다.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsMyCoupon]

    def get_queryset(self):
        """
        URL의 coupon_id를 바탕으로 해당 쿠폰에 속한 스탬프들을 조회합니다.
        """
        
        coupon_id: int = self.kwargs['coupon_id']
        return (Stamp.objects
               .filter(coupon_id=coupon_id)
               .select_related("receipt", "customer"))
    
    def get_serializer_class(self) -> drf_serializers.ModelSerializer:
        if self.request.method == 'GET':
            return StampCreateResponseSerializer
        
        return StampCreateRequestSerializer
    
    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['coupon_id'] = self.kwargs.get('coupon_id')
        return ctx
    
    def create(self, request, *args, **kwargs):
        """
        프론트에서 전달 받은 영수증 번호를 바탕으로, 해당 영수증 번호로 기발급된 스탬프를 체크한 후, 문제가 없으면 스탬프를 등록하고 해당 쿠폰의 전체 스탬프 목록을 돌려줍니다.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stamp = serializer.save()

        response_serializer = StampCreateResponseSerializer(stamp, context=self.get_serializer_context())
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer) -> Stamp:
        """
        시리얼라이저에 의해 저장된 데이터를 반환하도록 하여 응답용 시리얼라이저에 인스턴스를 넣을 수 있게 합니다.
        """

        return serializer.save()
