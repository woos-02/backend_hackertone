from django.db import models

# Create your models here.
class CouponBook(models.Model):
    """
    쿠폰북입니다.
    """
    customer = models.ForeignKey("accounts.models.User",
                                 on_delete=models.CASCADE,
                                 help_text="쿠폰북을 소유한 유저입니다.")
    design_json = models.JSONField(help_text="쿠폰북에 대한 디자인 정보가 JSON으로 저장되어 있습니다.")

class FavoriteCoupons(models.Model):
    """
    즐겨찾기한 쿠폰들입니다. 쿠폰북에서 조회합니다.
    """
    coupon = models.ForeignKey("coupons.models.Coupon",
                               on_delete=models.CASCADE,
                               help_text="즐겨찾기 한 쿠폰입니다.")
    couponbook = models.ForeignKey(CouponBook, on_delete=models.CASCADE, help_text="쿠폰북입니다.")
