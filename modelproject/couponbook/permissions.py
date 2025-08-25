from rest_framework.permissions import BasePermission

from .models import Coupon, CouponBook


class IsMyCouponBook(BasePermission):
    """
    본인의 쿠폰북인지 확인합니다.

    사용되는 뷰: CouponListView (permission), FavoriteCouponListView (permission)
    """

    def has_object_permission(self, request, view, obj: CouponBook) -> bool:
        """
        쿠폰북 인스턴스의 유저와 요청의 유저를 비교합니다.
        """
        return obj.user == request.user

    def has_permission(self, request, view) -> bool:
        """
        Path Parameter인 couponbook_id를 바탕으로 쿠폰북 인스턴스를 얻어 해당 쿠폰북의 유저와 현재 요청의 유저를 비교합니다.
        """
        couponbook_id = view.kwargs['couponbook_id']
        couponbook = CouponBook.objects.get(id=couponbook_id)
        return self.has_object_permission(request, view, couponbook)

class IsMyCoupon(BasePermission):
    """
    본인의 쿠폰인지 확인합니다.
    
    사용되는 뷰: CouponDetailView (object permission), StampListView (permission)
    """

    def has_object_permission(self, request, view, obj: Coupon) -> bool:
        """
        쿠폰 인스턴스에 연결된 쿠폰북의 유저와 요청의 유저를 비교합니다.
        """
        return obj.couponbook.user == request.user

    def has_permission(self, request, view) -> bool:
        """
        Path Parameter인 coupon_id를 바탕으로 쿠폰 인스턴스를 얻어 해당 쿠폰이 있는 쿠폰북의 유저와 현재 요청의 유저를 비교합니다.
        """
        coupon_id = view.kwargs['coupon_id']
        coupon = Coupon.objects.get(id=coupon_id)
        return self.has_object_permission(request, view, coupon)

class IsMyCouponForFavoriteAdd(IsMyCouponBook):
    """
    즐겨찾기 쿠폰 등록에 사용되는 권한입니다.
    """

    def has_object_permission(self, request, view, obj: Coupon | CouponBook) -> bool:
        """
        쿠폰 또는 쿠폰북 인스턴스에 연결된 쿠폰북의 유저와 요청의 유저를 비교합니다.
        """
        if isinstance(obj, Coupon):
            return obj.couponbook.user == request.user
        else:
            return obj.user == request.user
    
    def has_permission(self, request, view) -> bool:
        if request.method == 'POST' and super().has_permission(request, view):
            coupon_id = request.data['coupon']
            coupon = Coupon.objects.get(id=coupon_id)
            
            return self.has_object_permission(request, view, coupon)
        return super().has_permission(request, view)
