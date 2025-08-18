"""
큐레이션에서 예시로 사용하는 객체들이 정의되어 있습니다.
"""

class ExampleStamp:
    """
    예시 스탬프 객체입니다. 분석 프롬프트의 예시를 위해 사용되는 객체이며, 장고 모델로 사용되지 않습니다.
    """
    def __init__(self, created_at: str):
        """
        장고 모델인 Stamp는 created_at이 datetime이지만, 편의를 위해 여기에선 문자열로 사용합니다.
        """
        self.created_at = created_at

class ExamplePlace:
    """
    예시 가게 객체입니다. 분석 프롬프트의 예시를 위해 사용되는 객체이며, 장고 모델로 사용되지 않습니다.
    """
    def __init__(self, name: str):
        self.name = name
    
    def export_place_info(self) -> dict:
        """
        예시 쿠폰 객체에서 사용할 수 있도록, 예시 가게 객체의 가게 정보를 딕셔너리로 반환합니다.
        """
        place_dict = {}
        place_dict['name'] = self.name
        return place_dict

class ExampleCoupon:
    """
    예시 쿠폰 객체입니다. 분석 프롬프트의 예시를 위해 사용되는 객체이며, 장고 모델로 사용되지 않습니다.
    """
    def __init__(self, instance_id: int, place: ExamplePlace, max_stamps: int):
        """
        다음 인자를 받습니다. (모두 필수)
        - instance_id: 인스턴스의 id입니다. unique 제약은 없지만 실제 예시처럼 unique한 id를 지정할 것을 추천합니다.
        - place: 예시 가게 객체입니다.
        - max_stamps: 쿠폰을 완성하기 위해 필요한 스탬프의 개수입니다.
        """
        self.id = instance_id
        self.place = place
        self.max_stamps = max_stamps
        self.stamps: list[ExampleStamp] = []
    
    def add_stamp(self, stamp: ExampleStamp) -> None:
        """
        예시 스탬프 인스턴스를 인자로 받아 현재 쿠폰 인스턴스의 스탬프 목록에 추가합니다.
        """
        stamps: list[ExampleStamp] = self.stamps
        stamps.append(stamp)

    @property
    def current_stamps(self) -> int:
        """
        현재 스탬프 수입니다.
        """
        return len(self.stamps)
    
    @property
    def stamp_history(self) -> list[dict]:
        """
        현재 쿠폰의 스탬프 적립 이력입니다.
        """
        history_list: list[dict] = []
        stamps = sorted(self.stamps, key=lambda x: x.created_at) # 스탬프를 등록일 기준으로 정렬
        for count, stamp in enumerate(stamps, start=1):
            stamp_dict = {}
            stamp_dict['count'] = count
            stamp_dict['created_at'] = stamp.created_at
            history_list.append(stamp_dict)
        
        return history_list
    
    def export_coupon_data(self) -> dict:
        """
        큐레이션 프롬프트에서 이용할 수 있도록, 현재 인스턴스의 데이터를 딕셔너리로 반환합니다.
        """
        coupon_dict = {}
        coupon_dict['id'] = self.id
        data = {}
        data['place_info'] = self.place.export_place_info()
        data['max_stamps'] = self.max_stamps
        data['current_stamps'] = self.current_stamps
        data['stamp_history'] = self.stamp_history
        coupon_dict['data'] = data
        
        return coupon_dict

class ExampleStatistics:
    """
    예시 통계 객체입니다.
    """
    def __init__(self):
        self.coupons: list[ExampleCoupon] = []
    
    def add_coupon(self, coupon: ExampleCoupon):
        """
        예시 쿠폰 인스턴스를 현재 통계 인스턴스의 쿠폰 컬렉션에 추가합니다. 
        """
        self.coupons.append(coupon)
    
    def make_history(self) -> list[dict]:
        """
        쿠폰 사용 이력을 리스트로 만들어 반환합니다.
        """
        history_list: list[dict] = []
        coupons: list[ExampleCoupon] = self.coupons

        for coupon in coupons:
            coupon_data = coupon.export_coupon_data()
            history_list.append(coupon_data)
        
        return history_list

def get_example_statistics() -> ExampleStatistics:
    """
    예시 컨텐츠에서 이용할 통계 인스턴스를 생성해서 반환합니다.
    """
    statistics = ExampleStatistics()
    coupon_ids = [1, 2]
    places = [ExamplePlace("한식당"), ExamplePlace("일식당")]
    stamps = [ExampleStamp(f"2025-08-{i:02d}") for i in range(8, 16)] # 0: 8일 / 7: 15일
    max_stamps = [10, 10]
    stamp_ranges = [(8, 15), (11, 14)]
    stamps_index_offset = 8

    for coupon_id, place, max_stamp, stamp_range in zip(coupon_ids, places, max_stamps, stamp_ranges):
        coupon = ExampleCoupon(coupon_id, place, max_stamp)
        start, end = stamp_range
        for i in range(start, end+1):
            index = i - stamps_index_offset
            coupon.add_stamp(stamps[index])
        statistics.add_coupon(coupon)
    
    return statistics

def get_test_statistics() -> ExampleStatistics:
    """
    테스트용으로 사용할 임시 예시 통계 인스턴스를 생성해서 반환합니다.
    """
    statistics = ExampleStatistics()
    coupon_ids = [3, 5, 9]
    places = [ExamplePlace("중식당"), ExamplePlace("횟집"), ExamplePlace("고향설렁탕")]
    stamps = [ExampleStamp(f"2025-08-{i:02d}") for i in range(11, 19)] # 0: 11일 / 8: 19일
    max_stamps = [10, 10, 10]
    stamp_ranges = [(14, 15), (11, 13), (14, 18)]
    stamps_index_offset = 11

    for coupon_id, place, max_stamp, stamp_range in zip(coupon_ids, places, max_stamps, stamp_ranges):
        coupon = ExampleCoupon(coupon_id, place, max_stamp)
        start, end = stamp_range
        for i in range(start, end+1):
            index = i - stamps_index_offset
            coupon.add_stamp(stamps[index])
        statistics.add_coupon(coupon)
    
    return statistics
