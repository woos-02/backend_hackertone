from django.db import models

# Create your models here.

class CouponBook(models.Model):
    """
    쿠폰북 모델입니다. 실제 사용되는 쿠폰들은 쿠폰북에서 쿠폰을 역참조하는 형태로 조회됩니다.
    """
    user = models.OneToOneField("accounts.User",
                                 related_name='couponbook',
                                 on_delete=models.CASCADE,
                                 help_text="쿠폰북을 소유한 유저 id입니다.")

class Coupon(models.Model):
    """
    실제 사용되는 쿠폰입니다.
    """
    couponbook = models.ForeignKey(CouponBook,
                                   related_name='coupons',
                                   on_delete=models.CASCADE,
                                   help_text="해당 쿠폰이 등록되어 있는 쿠폰북 id입니다.")
    original_template = models.ForeignKey("CouponTemplate",
                                          related_name='coupons',
                                          on_delete=models.CASCADE,
                                          help_text="쿠폰 발행에 사용된 쿠폰 템플릿 id입니다. 유효성 검증에 사용합니다.")
    saved_at = models.DateTimeField(auto_now_add=True, help_text="쿠폰을 등록한 날짜와 시간입니다.")

class FavoriteCoupon(models.Model):
    """
    즐겨찾기 등록한 쿠폰입니다.
    """
    couponbook = models.ForeignKey(CouponBook,
                                   related_name='favorite_coupons',
                                   on_delete=models.CASCADE,
                                   help_text="해당 쿠폰이 등록되어 있는 쿠폰북 id입니다.")
    coupon = models.OneToOneField(Coupon,
                                  on_delete=models.CASCADE,
                                  help_text="즐겨찾기 등록한 쿠폰 id입니다.")
    added_at = models.DateTimeField(auto_now_add=True, help_text="즐겨찾기에 등록한 날짜와 시간입니다.")

class CouponTemplate(models.Model):
    """
    점주가 등록해서 게시중인 쿠폰 템플릿입니다.
    """
    valid_until = models.DateTimeField(default=None, help_text="쿠폰의 유효기간입니다.")
    first_n_persons = models.PositiveIntegerField(default=0, help_text="선착순 몇명까지 쿠폰이 발급한지를 의미합니다.")
    is_on = models.BooleanField(default=True, help_text="게시 중/비공개 여부를 불리언으로 나타냅니다.")
    # Todo: views 시리얼라이저 필드로 이동
    views = models.PositiveIntegerField(default=0, help_text="조회수를 의미합니다.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="점주가 쿠폰 템플릿을 등록한 날짜와 시간입니다.")
    place = models.ForeignKey("couponbook.Place",
                              related_name='coupon_templates',
                              on_delete=models.CASCADE,
                              help_text="해당 쿠폰과 연관된 매장 id입니다.",
                              null=True)

class RewardsInfo(models.Model):
    """
    한 쿠폰의 리워드 정보를 나타냅니다.
    """
    coupon_template = models.OneToOneField(CouponTemplate,
                                        related_name='reward_info',
                                        on_delete=models.CASCADE,
                                        help_text="어떤 쿠폰 템플릿 id에 있는 리워드 정보인지를 의미합니다.")
    amount = models.PositiveIntegerField(help_text="리워드를 지급하는 스탬프 횟수입니다.")
    reward = models.CharField(max_length=100, help_text="어떤 혜택이 있는지를 의미합니다.")

class Stamp(models.Model):
    """
    스탬프입니다.
    """
    coupon = models.ForeignKey(Coupon,
                               related_name='stamps',
                               on_delete=models.CASCADE,
                               help_text="어떤 쿠폰 id에 적립된 스탬프인지를 의미합니다.")
    receipt = models.OneToOneField('couponbook.Receipt',
                                       related_name='stamp',
                                       on_delete=models.CASCADE,
                                       help_text="해당 스탬프의 적립 근거가 되는 영수증 번호입니다.")
    customer = models.ForeignKey("accounts.User", on_delete=models.CASCADE, help_text="스탬프를 적립받은 고객 id입니다.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="스탬프가 적립된 날짜와 시간입니다.")

class Receipt(models.Model):
    """
    점주가 결제 완료 후 등록한 영수증입니다. 이 영수증과 일치해야 스탬프가 적립됩니다.
    """
    receipt_number = models.CharField(max_length=30, help_text="영수증 번호입니다. 중복되지 않습니다.", unique=True, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text="점주에 의해 영수증이 등록된 날짜와 시간입니다.")

class Place(models.Model):
    """
    가게 모델입니다.
    """
    name = models.CharField(max_length=20, help_text="가게 이름입니다.")
    address = models.CharField(max_length=50, help_text="가게 주소입니다. 지번 기준입니다. 예시) 서울특별시 동대문구 이문동 107")
    image_url = models.URLField(help_text="가게의 이미지가 담겨 있는 URL입니다.")
    opens_at = models.TimeField(help_text="영업 시작 시간입니다.")
    closes_at = models.TimeField(help_text="영업 종료 시간입니다.")
    # todo: 영업하는 요일 필드 추가
    last_order = models.TimeField(help_text="라스트오더 시간입니다.")
    tel = models.CharField(max_length=20, help_text="가게 전화번호입니다.")