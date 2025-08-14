from django.db import models


# Create your models here.
class CouponBook(models.Model):
    """
    쿠폰북 모델입니다. 실제 사용되는 쿠폰들은 쿠폰북에서 쿠폰을 역참조하는 형태로 조회됩니다.
    """
    user = models.ForeignKey("accounts.User",
                                 related_name='couponbook',
                                 on_delete=models.CASCADE,
                                 help_text="쿠폰북을 소유한 유저 id입니다.")
    design_json = models.JSONField(help_text="쿠폰북에 대한 디자인 정보가 JSON으로 저장되어 있습니다.")

class Coupon(models.Model):
    """
    실제 사용되는 쿠폰입니다.
    """
    couponbook = models.ForeignKey(CouponBook,
                                   related_name='coupons',
                                   on_delete=models.CASCADE,
                                   help_text="해당 쿠폰이 등록되어 있는 쿠폰북 id입니다.")
    original_template = models.ForeignKey("CouponTemplate",
                                          on_delete=models.CASCADE,
                                          help_text="쿠폰 발행에 사용된 쿠폰 템플릿 id입니다. 유효성 검증에 사용합니다.")
    image_url = models.URLField(help_text="쿠폰의 이미지가 담겨 있는 URL입니다.")
    max_stamps = models.PositiveIntegerField(help_text="쿠폰 완성까지 필요한 총 스탬프의 개수입니다.")
    is_favorite = models.BooleanField(default=False, help_text="해당 쿠폰을 즐겨찾기했는지의 여부를 나타냅니다.")
    is_completed = models.BooleanField(default=False, help_text="쿠폰 완성 여부를 나타냅니다.")

class CouponTemplate(models.Model):
    """
    점주가 등록해서 게시중인 쿠폰 템플릿입니다.
    """
    valid_until = models.DateTimeField(default=None, help_text="쿠폰의 유효기간입니다.")
    first_n_persons = models.PositiveIntegerField(default=0, help_text="선착순 몇명까지 쿠폰이 발급한지를 의미합니다.")
    image_url = models.URLField(help_text="쿠폰의 이미지가 담겨 있는 URL입니다.")
    max_stamps = models.PositiveIntegerField(help_text="쿠폰 완성까지 필요한 총 스탬프의 개수입니다.")
    is_on = models.BooleanField(default=True, help_text="게시 중/비공개 여부를 불리언으로 나타냅니다.")
    views = models.PositiveIntegerField(default=0, help_text="조회수를 의미합니다.")
    saves = models.PositiveIntegerField(default=0, help_text="저장된 횟수입니다.")
    uses = models.PositiveIntegerField(default=0, help_text="사용된 횟수입니다.")

class RewardsInfo(models.Model):
    """
    한 쿠폰의 리워드 정보를 나타냅니다.
    """
    coupon_template = models.ForeignKey(CouponTemplate,
                                        on_delete=models.CASCADE,
                                        help_text="어떤 쿠폰 템플릿 id에 있는 리워드 정보인지를 의미합니다.")
    amount = models.PositiveIntegerField(help_text="리워드를 지급하는 스탬프 횟수입니다.")
    reward = models.CharField(help_text="어떤 혜택이 있는지를 의미합니다.")

class Stamp(models.Model):
    """
    스탬프입니다.
    """
    coupon = models.ForeignKey(Coupon,
                               related_name='stamps',
                               on_delete=models.CASCADE,
                               help_text="어떤 쿠폰 id에 적립된 스탬프인지를 의미합니다.")
    related_payment = models.ForeignKey("payment.PaymentHistory",
                                        on_delete=models.CASCADE,
                                        help_text="해당 스탬프의 적립 근거가 되는 결제 내역 id입니다.")
    customer = models.ForeignKey("accounts.User", on_delete=models.CASCADE, help_text="스탬프를 적립받은 고객 id입니다.")