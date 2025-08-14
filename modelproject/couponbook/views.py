from accounts.models import User
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

from modelproject.couponbook.models import CouponBook

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
class CouponListView(ListAPIView):
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
    serializer_class = CouponDetailResponseSserializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Coupon.objects.all()
    lookup_url_kwarg = 'coupon_id'


# -------------------------------- 스탬프 ---------------------------------
@extend_schema_view(
    get=extend_schema(
        description="쿠폰 id에 해당하는 쿠폰에 속한 스탬프들의 목록을 가져옵니다."
    )
)
class StampListView(ListAPIView):
    """
    한 쿠폰 내의 스탬프 목록을 조회하는 뷰입니다.
    """
    serializer_class = StampListResponseSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        URL의 coupon_id를 바탕으로 해당 쿠폰에 속한 스탬프들을 조회합니다.
        """
        coupon_id: int = self.kwargs['coupon_id']
        return Stamp.objects.filter(coupon_id=coupon_id)

@extend_schema_view(
    get=extend_schema(
        description="스탬프 id에 해당하는 쿠폰을 조회합니다. " \
            "스탬프 목록 조회와는 다르게 스탬프 id를 path parmaeter로 취하는 점에 주의해야 합니다.",
    )
)
class StampDetailView(RetrieveAPIView):
    """
    한 스탬프를 조회하는 뷰입니다. 스탬프 id에 해당하는 쿠폰을 조회합니다.
    """
    serializer_class = StampDetailSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Stamp.objects.all()
    lookup_url_kwarg = 'stamp_id'