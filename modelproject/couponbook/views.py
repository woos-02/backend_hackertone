from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.generics import (ListAPIView, ListCreateAPIView,
                                     RetrieveAPIView)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import *
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
        description="현재 로그인된 유저의 유저 id(username이 아닙니다)에 해당하는 쿠폰북을 조회합니다."
    )
)
class CouponBookDetailView(RetrieveAPIView):
    """
    한 쿠폰북을 조회하는 뷰입니다. 로그인된 유저의 유저 id에 해당하는 쿠폰북을 조회합니다.
    """ 
    serializer_class = CouponBookResponseSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

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
        description="쿠폰북 id에 해당하는 쿠폰북에 속한 쿠폰들의 목록을 가져옵니다."
    )
)
class CouponListView(ListCreateAPIView):
    """
    쿠폰 목록에 관련된 뷰입니다. 쿠폰북에 속한 쿠폰들의 목록을 가져옵니다.
    """
    serializer_class = CouponListResponseSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        URL의 couponbook_id를 바탕으로 해당 쿠폰북에 속한 쿠폰들을 조회합니다.
        """
        couponbook_id: int = self.kwargs['couponbook_id']
        return Coupon.objects.filter(couponbook_id=couponbook_id)
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CouponListResponseSerializer
        return CouponListRequestSerializer
    
    def create(self, request, *args, **kwargs):
        """
        쿠폰 템플릿 id를 받아서, 해당 쿠폰 템플릿을 바탕으로 실사용 쿠폰을 생성합니다.
        """
        couponbook_id = self.kwargs['couponbook_id']
        couponbook = get_object_or_404(CouponBook, id=couponbook_id)
        serializer = CouponListRequestSerializer(data=request.data, context={'request': request, 'couponbook': couponbook})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

@extend_schema_view(
    get=extend_schema(
        description="쿠폰 id에 해당하는 쿠폰을 조회합니다. " \
            "쿠폰 목록 조회와는 다르게 쿠폰 id를 path parmaeter로 취하는 점에 주의해야 합니다.",
    )
)
class CouponDetailView(RetrieveAPIView):
    """
    한 쿠폰을 조회하는 뷰입니다. 쿠폰 id에 해당하는 쿠폰을 조회합니다.
    """
    serializer_class = CouponDetailResponseSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Coupon.objects.all()
    lookup_url_kwarg = 'coupon_id'


# ----------------------------- 쿠폰 템플릿 -------------------------------
@extend_schema_view(
    get=extend_schema(
        description="현재 게시중으로 설정된 쿠폰 템플릿들의 목록을 가져옵니다."
    )
)
class CouponTemplateListView(ListAPIView):
    """
    쿠폰 템플릿들을 조회하는 뷰입니다.
    """
    serializer_class = CouponTemplateListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = CouponTemplate.objects.filter(is_on=True)

@extend_schema_view(
    get=extend_schema(
        description="현재 게시중으로 설정된 쿠폰 템플릿들 중 쿠폰 템플릿 id에 해당하는 쿠폰 템플릿을 가져옵니다."
    )
)
class CouponTemplateDetailView(RetrieveAPIView):
    """
    한 쿠폰 템플릿을 조회하는 뷰입니다.
    """
    serializer_class = CouponTemplateListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = CouponTemplate.objects.filter(is_on=True)
    lookup_url_kwarg = 'coupon_template_id'


# -------------------------------- 스탬프 ---------------------------------
@extend_schema_view(
    get=extend_schema(
        description="쿠폰 id에 해당하는 쿠폰에 속한 스탬프들의 목록을 가져옵니다."
    ),
    post=extend_schema(
        description="영수증 번호를 바탕으로 영수증이 존재하는지, 스탬프가 이미 등록되지 않았는지 확인하고, 두 조건 모두 만족하면 스탬프를 등록합니다."
    )
)
class StampListView(ListCreateAPIView):
    """
    스탬프 목록 조회 및 스탬프 적립(등록)과 관련된 뷰입니다.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        URL의 coupon_id를 바탕으로 해당 쿠폰에 속한 스탬프들을 조회합니다.
        """
        coupon_id: int = self.kwargs['coupon_id']
        return Stamp.objects.filter(coupon_id=coupon_id)
    
    def get_serializer_class(self) -> serializers.ModelSerializer:
        if self.request.method == 'GET':
            return StampListResponseSerializer
        
        return StampListRequestSerializer
    
    def create(self, request, *args, **kwargs):
        """
        프론트에서 전달 받은 영수증 번호를 바탕으로, 해당 영수증 번호로 기발급된 스탬프를 체크한 후, 문제가 없으면 스탬프를 등록합니다.
        """
        coupon_id: int = self.kwargs['coupon_id']

        # request의 data에는 영수증 번호만 들어 있고, 시리얼라이저의 create에서 context를 통해 쿠폰 id와 유저를 등록함
        serializer = StampListRequestSerializer(data=request.data, context={'request': request, 'coupon_id': coupon_id})
        # 시리얼라이저의 유효성 검사에서 기발급된 스탬프 확인 및 등록된 영수증 확인
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)