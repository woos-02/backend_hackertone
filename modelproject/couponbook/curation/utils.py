from accounts.models import User
from couponbook.models import *
from couponbook.serializers import PlaceDetailResponseSerializer


class UserStatistics:
    """
    유저의 쿠폰북 이용 통계 클래스입니다. AI의 큐레이션 기능에 활용됩니다.
    """
    def __init__(self, user: User):
        """
        유저 인스턴스를 인자로 전달해야 합니다.
        """
        self.user: User = user

    @property
    def own_couponbook(self):
        """
        해당 유저의 쿠폰북을 가져옵니다.
        """
        try:
            couponbook = CouponBook.objects.get(user=self.user)
            return couponbook
        except CouponBook.DoesNotExist:
            print("유저의 쿠폰북이 존재하지 않습니다.")
            
    
    def extract_place_info(self, place: Place) -> dict[str, str]:
        """
        가게 인스턴스를 받아서, 가게의 정보를 딕셔너리 안에 넣어서 반환합니다.
        """
        place_info = {}
        place_info['name'] = place.name
        place_info['address'] = place.address
        return place_info
    
    def calc_current_stamps(self, coupon: Coupon) -> int:
        """
        현재까지 적립된 스탬프 수를 계산합니다.
        """
        stamps = coupon.stamps
        return stamps.count()
    
    def calc_max_stamps(self, coupon_template: CouponTemplate) -> int:
        """
        쿠폰 완성을 위해 스탬프가 몇개 필요한지를 계산합니다.
        """
        reward_info: RewardsInfo = coupon_template.reward_info
        return reward_info.amount
    
    def make_stamp_history(self, coupon: Coupon) -> list[dict]:
        """
        해당 쿠폰의 스탬프 적립 히스토리를 만듭니다.
        """
        stamps = coupon.stamps.order_by('created_at')
        history_list = []
        for number, stamp in enumerate(stamps, start=1):
            stamp_data = {}
            stamp_data['count'] = number
            stamp_data['created_at'] = stamp.created_at
            history_list.append(stamp_data)
        return history_list
    
    def make_coupon_data(self, coupon: Coupon) -> dict:
        """
        쿠폰의 데이터를 만들어 딕셔너리로 반환합니다.
        """
        data = {}
        original_template = coupon.original_template
        data['place_info'] = self.extract_place_info(original_template.place)
        data['max_stamps'] = self.calc_max_stamps(original_template)
        data['current_stamps'] = self.calc_current_stamps(coupon)
        data['stamp_history'] = self.make_stamp_history(coupon)
        return data
    
    def make_history(self) -> list[dict]:
        """
        현재 보유하고 있는 쿠폰과, 쿠폰에 연결된 가게, 스탬프 적립 기록을 만들어 반환합니다.
        """
        coupons = Coupon.objects.filter(couponbook=self.own_couponbook)
        history = []
        for coupon in coupons:
            coupon_dict = {}
            coupon_dict['id'] = coupon.id
            coupon_dict['data'] = self.make_coupon_data(coupon)
            history.append(coupon_dict)
        return history