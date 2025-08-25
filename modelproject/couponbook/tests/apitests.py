from datetime import timedelta
from time import sleep

from accounts.models import User
from couponbook.models import *
from django.utils.timezone import now
from rest_framework.test import APITestCase

from .decorators import print_success_message


# API(뷰) 관련 테스트 케이스
class CouponBookViewTestCase(APITestCase):
    """
    쿠폰북 관련 테스트 케이스입니다.
    """

    @print_success_message("본인의 쿠폰만 보이는지 테스트")
    def test_only_my_coupon(self):
        """
        오직 본인의 쿠폰만 보여야 합니다. 다른 유저의 쿠폰은 보이면 안됩니다. 프라이버시를 지켜줍시다..
        """

        # 계정을 2개 생성
        user1 = User.objects.create(username='test', password='1234')
        user2 = User.objects.create(username='test2', password='1234')

        # user1로 로그인
        self.client.force_authenticate(user=user1)
        r1_user1 = self.client.get('/couponbook/couponbooks/1/coupons/')
        self.assertEqual(r1_user1.status_code, 200) # 본인의 쿠폰들이므로 200
        r2_user1 = self.client.get('/couponbook/couponbooks/2/coupons/')
        self.assertEqual(r2_user1.status_code, 403, "프라이버시가 지켜지지 않고 있습니다..") # 남의 쿠폰들이므로 Forbidden

        # user2로 로그인
        self.client.force_authenticate(user=user2)
        r1_user2 = self.client.get('/couponbook/couponbooks/1/coupons/')
        self.assertEqual(r1_user2.status_code, 403, "프라이버시가 지켜지지 않고 있습니다..") # 남의 쿠폰들이므로 Forbidden
        r2_user2 = self.client.get('/couponbook/couponbooks/2/coupons/')
        self.assertEqual(r2_user2.status_code, 200) # 본인의 쿠폰들이므로 200

class FavoriteCouponTestCase(APITestCase):
    """
    쿠폰 즐겨찾기 기능 관련 테스트 케이스입니다.
    """

    def setUp(self):
        """
        각 테스트 메소드 진행 전에 즐겨찾기로 등록할 쿠폰을 미리 만들어 둡니다. 유저 생성 및 로그인, 쿠폰 등록을 미리 실행합니다.
        """

        # 법정동 주소 생성
        legal_district_dict = {
            'code_in_law': '1123011000',
            'province': '서울특별시',
            'city': '동대문구',
            'district': '이문동',
        }
        legal_district = LegalDistrict.objects.create(**legal_district_dict)
        
        # 가게 생성
        place_dict = {
            'name': '한국외대 서울캠퍼스',
            'address_district': legal_district,
            'address_rest': '1234',
            'image_url': 'aaa.jpg',
            'opens_at': now().time(),
            'closes_at': now().time(),
            'tags': '대학교',
            'last_order': now().time(),
            'tel': '02-xxxx-xxxx',
            'owner': None,
        }
        place = Place.objects.create(**place_dict)

        # 쿠폰 템플릿 생성
        original_template_dict = {
            'first_n_persons': 10,
            'is_on': True,
            'place': place
        }
        coupon_template = CouponTemplate.objects.create(**original_template_dict)

        # 유저 생성 및 로그인
        user = User.objects.create(username='test', password='1234')
        self.client.force_authenticate(user=user)

        # 쿠폰 등록
        coupon_dict = {
            'couponbook': CouponBook.objects.get(user=user),
            'original_template': coupon_template,
        }
        Coupon.objects.create(**coupon_dict)

        return super().setUp()

    @print_success_message("즐겨찾기 쿠폰 등록, 조회, 삭제 테스트")
    def test_favorite_coupon(self):
        """
        즐겨찾기 쿠폰 기능 테스트 메소드입니다.
        """

        # 현재 즐겨찾기 개수 조회 (0개여야 함)
        r = self.client.get('/couponbook/own-couponbook/')
        self.assertEqual(r.data['favorite_counts'], 0, "귀신이 들었나보네요.")
        
        # 즐겨찾기 쿠폰 추가
        self.client.post('/couponbook/couponbooks/1/favorites/', {'coupon': 1})
        r = self.client.get('/couponbook/own-couponbook/')
        self.assertEqual(r.data['favorite_counts'], 1, 
                         f"예상된 즐겨찾기 쿠폰 개수와 다릅니다. ({r.data['favorite_counts']}, 1)")
        
        # 즐겨찾기 쿠폰 삭제
        self.client.delete('/couponbook/own-couponbook/favorites/1/')
        r = self.client.get('/couponbook/own-couponbook/')
        self.assertEqual(r.data['favorite_counts'], 0, 
                         f"예상된 즐겨찾기 쿠폰 개수와 다릅니다. ({r.data['favorite_counts']}, 0)")
    
    @print_success_message("쿠폰 템플릿 삭제로 인한 즐겨찾기 쿠폰 삭제 테스트")
    def test_coupon_template_delete_and_favorite_coupon_cascade(self):
        """
        쿠폰이 삭제될 시 즐겨찾기 쿠폰도 같이 삭제되는지 테스트하는 메소드입니다.
        """

        # 현재 즐겨찾기 개수 조회 (0개여야 함)
        r = self.client.get('/couponbook/own-couponbook/')
        self.assertEqual(r.data['favorite_counts'], 0, "귀신이 들었나보네요.")

        # 즐겨찾기 쿠폰 추가
        self.client.post('/couponbook/couponbooks/1/favorites/', {'coupon': 1})
        r = self.client.get('/couponbook/own-couponbook/')
        self.assertEqual(r.data['favorite_counts'], 1, 
                         f"예상된 즐겨찾기 쿠폰 개수와 다릅니다. ({r.data['favorite_counts']}, 1)")

        # 쿠폰 템플릿 삭제
        coupon_template = CouponTemplate.objects.get(id=1)
        coupon_template.delete()

        # 즐겨찾기 쿠폰 개수 확인 (0개여야 함)
        r = self.client.get('/couponbook/own-couponbook/')
        self.assertEqual(r.data['favorite_counts'], 0, 
                         f"예상된 즐겨찾기 쿠폰 개수와 다릅니다. ({r.data['favorite_counts']}, 1)")
    
    @print_success_message("본인이 소유하지 않은 쿠폰북의 즐겨찾기 쿠폰 목록을 열람 불가능한지 테스트")
    def test_list_others_favorite_coupons(self):
        """
        본인이 소유하지 않은 쿠폰북의 즐겨찾기 쿠폰 목록이 열람 불가능한지 테스트하는 테스트 메소드입니다.
        """
        
        # 또다른 유저 생성 및 로그인
        user2 = User.objects.create(username='test2', password='1234')
        self.client.force_authenticate(user=user2)

        # 유저 2가 유저 1의 즐겨찾기 쿠폰 열람 시도
        r = self.client.get('/couponbook/couponbooks/1/favorites/')
        self.assertEqual(r.status_code, 403, "쿠폰을 엿보기 당했습니다..")

    @print_success_message("본인이 소유하지 않은 쿠폰을 즐겨찾기 등록 불가능한지 테스트")
    def test_add_others_coupon_as_favorite(self):
        """
        본인이 소유하지 않은 쿠폰을 즐겨찾기 등록할 수 없는지 테스트하는 테스트 메소드입니다.
        """

        # 또다른 유저 생성 및 로그인
        user2 = User.objects.create(username='test2', password='1234')
        self.client.force_authenticate(user=user2)

        # 유저 2가 유저 1의 쿠폰을 즐겨찾기 등록 시도
        r = self.client.post('/couponbook/couponbooks/2/favorites/', {'coupon': 1})
        self.assertEqual(r.status_code, 403, "타인의 쿠폰을 어떻게 즐겨찾기에 등록한걸까요..")

class ResponseTestCase(APITestCase):
    """
    필요한 데이터를 반환하고 있는지 테스트하는 테스트 케이스입니다.

    필요한 데이터는 쿠폰북 디자인을 바탕으로 지정되었습니다. 다음의 규칙을 따릅니다.
    1) 연관 데이터, 같은 모델 내의 데이터는 최대한 묶습니다.
    2) 프론트의 편의를 위해 화면의 위 -> 아래 순서로 필드 순서를 지정합니다.
    3) 최대한 기존의 변수명을 유지합니다. 프론트의 코드에 주는 영향을 최소화합니다.

    특히, 시리얼라이저 리팩토링에서 중요한 기준이 되는 테스트케이스입니다.
    """

    def setUp(self):
        """
        각 테스트 메소드 진행 전에 미리 필요한 데이터를 세팅합니다.

        시연에 필요한 데이터들의 세팅 및 유저의 로그인 과정을 실행합니다. 이후의 과정은 테스트 메소드를 통해 구간별로 테스트합니다.
        """
        # 법정동 주소 생성
        legal_district_dict = {
            'code_in_law': '1123011000',
            'province': '서울특별시',
            'city': '동대문구',
            'district': '이문동',
        }
        legal_district = LegalDistrict.objects.create(**legal_district_dict)
        
        # 가게 생성
        place_dict = {
            'name': '한국외대 서울캠퍼스',
            'address_district': legal_district,
            'address_rest': '1234',
            'image_url': 'aaa.jpg',
            'opens_at': now().time(),
            'closes_at': now().time(),
            'tags': '대학교',
            'last_order': now().time(),
            'tel': '02-xxxx-xxxx',
            'owner': None,
        }
        place = Place.objects.create(**place_dict)

        # 쿠폰 템플릿 생성
        original_template_dict = {
            'first_n_persons': 10,
            'is_on': True,
            'place': place
        }
        coupon_template = CouponTemplate.objects.create(**original_template_dict)

        # 리워드 정보 생성
        reward_info_dict = {
            'coupon_template': coupon_template,
            'amount': 10,
            'reward': '대학원 입학권 무료'
        }
        RewardsInfo.objects.create(**reward_info_dict)

        # 영수증 생성
        for i in range(3):
            Receipt.objects.create(receipt_number=f'{i:08d}')

        # 유저 생성 및 로그인
        user = User.objects.create(username='test', password='1234')
        self.client.force_authenticate(user=user)

        return super().setUp()

    @print_success_message("쿠폰북 정보 조회 시 필요한 데이터가 반환되는지 테스트")
    def test_couponbook_response(self):
        """
        쿠폰북 정보 조회가 필요한 데이터를 반환하고 있는지 테스트하는 테스트 메소드입니다.

        필요한 데이터: 즐겨찾기 쿠폰 수, 저장한 쿠폰 수, 스탬프 수
        """

        r = self.client.get('/couponbook/own-couponbook/')
        keys = r.data.keys()

        for key in ('favorite_counts', 'coupon_counts', 'stamp_counts'):
            self.assertEqual(key in keys, True, f"필요한 데이터가 빠졌습니다! {key}")
    
    @print_success_message("쿠폰 목록 조회 시 필요한 데이터가 반환되는지 테스트")
    def test_coupon_list_response(self):
        """
        쿠폰 목록 조회가 필요한 데이터를 반환하고 있는지 테스트하는 테스트 메소드입니다.

        필요한 데이터: 개별 쿠폰 url, 가게 정보, 리워드 정보, 현재 스탬프 개수, 남은 기간
            - 가게 정보: 가게 이미지 url, 가게 이름
            - 리워드 정보: 완성을 위해 필요한 개수, 리워드
        """

        r = self.client.post('/couponbook/couponbooks/1/coupons/', {'original_template': 1})
        self.assertEqual(r.status_code, 201, "쿠폰 등록에 실패한 것 같습니다...") # 201 Created

        r = self.client.get('/couponbook/couponbooks/1/coupons/')
        keys = r.data[0].keys()

        for key in ('coupon_url', 'place', 'reward_info',
                    'current_stamps', 'days_remaining'):
            self.assertEqual(key in keys, True, f"필요한 데이터가 빠졌습니다! {key}")
        
        place_keys = r.data[0]['place'].keys()

        for key in ('image_url', 'name'):
            self.assertEqual(key in place_keys, True, f"필요한 데이터가 빠졌습니다! {key}")
        
        reward_info_keys = r.data[0]['reward_info'].keys()
        
        for key in ('amount', 'reward'):
            self.assertEqual(key in reward_info_keys, True, f"필요한 데이터가 빠졌습니다! {key}")
    
    @print_success_message("단일 쿠폰 조회 시 필요한 데이터가 반환되는지 테스트")
    def test_coupon_detail_response(self):
        """
        단일 쿠폰 정보 조회가 필요한 데이터를 반환하고 있는지 테스트하는 테스트 메소드입니다.
        
        필요한 데이터: 즐겨찾기 여부, 리워드 정보, 현재 스탬프 개수, 매장 정보
            - 리워드 정보: 완성을 위해 필요한 개수, 리워드
            - 매장 정보: 가게 이미지, 위치, 오픈 시간, 종료 시간, 라스트 오더, 연락처
        """

        r = self.client.post('/couponbook/couponbooks/1/coupons/', {'original_template': 1})
        self.assertEqual(r.status_code, 201, "쿠폰 등록에 실패한 것 같습니다...")
        
        r = self.client.get('/couponbook/coupons/1/')
        keys = r.data.keys()

        for key in ('is_favorite', 'reward_info',
                    'current_stamps', 'place'):
            self.assertEqual(key in keys, True, f"필요한 데이터가 빠졌습니다! {key}")

        # 리워드 정보에 대한 테스트
        reward_info = r.data['reward_info']
        reward_info_keys = reward_info.keys()

        for key in ('amount', 'reward'):
            self.assertEqual(key in reward_info_keys, True, f"필요한 데이터가 빠졌습니다! {key}")
        
        # 가게 정보에 대한 테스트
        place = r.data['place']
        place_keys = place.keys()

        for key in ('image_url', 'address', 'opens_at', 'closes_at', 'last_order', 'tel'):
            self.assertEqual(key in place_keys, True, f"필요한 데이터가 빠졌습니다! {key}")
    
    @print_success_message("스탬프를 적립 시 필요한 데이터가 반환되는지 테스트")
    def test_stamp_add_response(self):
        """
        스탬프를 적립할 시 필요한 데이터가 반환되는지 테스트하는 테스트 메소드입니다.

        필요한 데이터: 현재 스탬프 개수 (방금 적립된 스탬프 포함)
        """

        r = self.client.post('/couponbook/couponbooks/1/coupons/', {'original_template': 1})
        self.assertEqual(r.status_code, 201, "쿠폰 등록에 실패한 것 같습니다...")

        r = self.client.post('/couponbook/coupons/1/stamps/', {'receipt': f'{0:08d}'})
        self.assertEqual(r.status_code, 201, "스탬프 적립에 실패한 것 같습니다...")

        self.assertEqual('current_stamps' in r.data.keys(), True, "필요한 데이터가 빠졌습니다! current_stamps")
    
    @print_success_message("쿠폰 템플릿 큐레이션 테스트")
    def test_coupon_template_curation_test(self):
        """
        쿠폰 큐레이션이 정상 작동하는지 테스트하는 테스트 메소드입니다.
        """

        # r = self.client.post('/couponbook/couponbooks/1/coupons/', {'original_template': 1})
        # self.assertEqual(r.status_code, 201, "쿠폰 등록에 실패한 것 같습니다...")

        r = self.client.get('/couponbook/own-couponbook/curation/')
        self.assertEqual(r.status_code, 200, "무언가 잘못되었습니다...")

class StampTestCase(APITestCase):
    """
    스탬프에 관련된 테스트 케이스입니다.
    """

    def setUp(self):
        """
        스탬프 적립을 위해 필요한 가게, 영수증, 유저 등을 세팅합니다. 쿠폰 템플릿부터 테스트 메소드에서 생성합니다.
        """

        # 법정동 주소 생성
        legal_district_dict = {
            'code_in_law': '1123011000',
            'province': '서울특별시',
            'city': '동대문구',
            'district': '이문동',
        }
        legal_district = LegalDistrict.objects.create(**legal_district_dict)
        
        # 가게 생성
        place_dict = {
            'name': '한국외대 서울캠퍼스',
            'address_district': legal_district,
            'address_rest': '1234',
            'image_url': 'aaa.jpg',
            'opens_at': now().time(),
            'closes_at': now().time(),
            'tags': '대학교',
            'last_order': now().time(),
            'tel': '02-xxxx-xxxx',
            'owner': None,
        }
        Place.objects.create(**place_dict)

        # 영수증 생성
        for i in range(3):
            Receipt.objects.create(receipt_number=f'{i:08d}')

        # 유저 생성 및 로그인
        user = User.objects.create(username='test', password='1234')
        self.client.force_authenticate(user=user)

        return super().setUp()
    
    @print_success_message("이미 완성된 쿠폰에 스탬프 적립되지 않는지 테스트")
    def test_new_stamp_on_completed_coupon(self):
        """
        이미 완성된 쿠폰에 스탬프가 적립되지 않는지 테스트하는 테스트 메소드입니다.
        """

        # 쿠폰 템플릿 생성
        original_template_dict = {
            'first_n_persons': 10,
            'is_on': True,
            'place': Place.objects.get(id=1)
        }
        coupon_template = CouponTemplate.objects.create(**original_template_dict)

        # 리워드 정보 생성
        reward_info_dict = {
            'coupon_template': coupon_template,
            'amount': 2,
            'reward': '대학원 입학권 무료'
        }
        RewardsInfo.objects.create(**reward_info_dict)

        # 쿠폰 생성
        r = self.client.post('/couponbook/couponbooks/1/coupons/', {'original_template': 1})
        self.assertEqual(r.status_code, 201, "쿠폰 등록에 실패한 것 같습니다...")

        # 쿠폰 완성
        for i in range(2):
            r = self.client.post('/couponbook/coupons/1/stamps/', {'receipt': f"{i:08d}"})
        
        # 추가적인 적립 안되어야 함
        r = self.client.post('/couponbook/coupons/1/stamps/', {'receipt': f"{i+1:08d}"})
        self.assertEqual(r.status_code, 400, "한계를 돌파해버렸습니다!")

    @print_success_message("기간 만료된 쿠폰에 스탬프 적립되지 않는지 테스트")
    def test_new_stamp_on_expired_coupon(self):
        """
        유효기간이 지난 쿠폰에 스탬프가 적립되지 않는지 테스트하는 테스트 메소드입니다.
        """

        # 쿠폰 템플릿 생성
        original_template_dict = {
            'first_n_persons': 10,
            'valid_until': now() + timedelta(seconds=5), # now()로 설정하면 즉시 만료되므로, now()에 timedelta seconds를 조금 추가
            'is_on': True,
            'place': Place.objects.get(id=1)
        }
        coupon_template = CouponTemplate.objects.create(**original_template_dict)

        # 리워드 정보 생성
        reward_info_dict = {
            'coupon_template': coupon_template,
            'amount': 1,
            'reward': '대학원 입학권 무료'
        }
        RewardsInfo.objects.create(**reward_info_dict)

        # 쿠폰 생성
        r = self.client.post('/couponbook/couponbooks/1/coupons/', {'original_template': 1})
        self.assertEqual(r.status_code, 201, "쿠폰 등록에 실패한 것 같습니다...")

        # 유효기간이 지나도록 5초를 기다림
        sleep(5)

        # 스탬프 적립
        r = self.client.post('/couponbook/coupons/1/stamps/', {'receipt': f"{1:08d}"})
        self.assertEqual(r.status_code, 400, "기간 만료된 쿠폰에 스탬프가 적립되어 버렸습니다!")
    
    @print_success_message("본인 소유가 아닌 쿠폰을 사용했을 때 스탬프가 적립되지 않는지 테스트")
    def test_stamp_only_for_mine(self):
        """
        본인 소유의 쿠폰을 사용했을 때에만 스탬프가 적립되는지 테스트하는 테스트 메소드입니다.
        """

        # 쿠폰 템플릿 생성
        original_template_dict = {
            'first_n_persons': 10,
            'is_on': True,
            'place': Place.objects.get(id=1)
        }
        coupon_template = CouponTemplate.objects.create(**original_template_dict)

        # 리워드 정보 생성
        reward_info_dict = {
            'coupon_template': coupon_template,
            'amount': 2,
            'reward': '대학원 입학권 무료'
        }
        RewardsInfo.objects.create(**reward_info_dict)

        # setUp에서 생성된 유저로 로그인
        user1 = User.objects.get(id=1)
        self.client.force_authenticate(user=user1)
        
        # user1의 쿠폰 생성
        r = self.client.post('/couponbook/couponbooks/1/coupons/', {'original_template': 1})
        self.assertEqual(r.status_code, 201, "쿠폰 등록에 실패한 것 같습니다...")

        # user2 생성
        user2 = User.objects.create(username='test2', password='1234')
        self.client.force_authenticate(user=user2)

        # user2의 쿠폰 생성
        r = self.client.post('/couponbook/couponbooks/2/coupons/', {'original_template': 1})
        self.assertEqual(r.status_code, 201, "쿠폰 등록에 실패한 것 같습니다...")

        # user1로 다시 로그인 및 user2의 쿠폰에 스탬프 적립 시도
        self.client.force_authenticate(user=user1)
        r = self.client.post('/couponbook/coupons/2/stamps/', {'receipt_number': f'{1:08d}'})
        self.assertEqual(r.status_code, 403, "쿠폰이 도난되었습니다!")

        # user2로 다시 로그인 및 user2의 쿠폰에 스탬프 적립 시도
        self.client.force_authenticate(user=user2)
        r = self.client.post('/couponbook/coupons/1/stamps/', {'receipt_number': f'{2:08d}'})
        self.assertEqual(r.status_code, 403, "쿠폰이 도난되었습니다!")

class ExpiredCouponTemplateTestCase(APITestCase):
    """
    유효기간이 만료된 쿠폰 템플릿에 대한 테스트케이스입니다.
    """

    def setUp(self):
        # 법정동 주소 생성
        legal_district_dict = {
            'code_in_law': '1123011000',
            'province': '서울특별시',
            'city': '동대문구',
            'district': '이문동',
        }
        legal_district = LegalDistrict.objects.create(**legal_district_dict)
        
        # 가게 생성
        place_dict = {
            'name': '한국외대 서울캠퍼스',
            'address_district': legal_district,
            'address_rest': '1234',
            'image_url': 'aaa.jpg',
            'opens_at': now().time(),
            'closes_at': now().time(),
            'tags': '대학교',
            'last_order': now().time(),
            'tel': '02-xxxx-xxxx',
            'owner': None,
        }
        place = Place.objects.create(**place_dict)

        # 쿠폰 템플릿 생성
        original_template_dict = {
            'valid_until': now(),
            'first_n_persons': 10,
            'is_on': True,
            'place': place
        }
        coupon_template = CouponTemplate.objects.create(**original_template_dict)

        reward_info_dict = {
            'amount': 5,
            'reward': '대학원 무료',
            'coupon_template': coupon_template,
        }
        RewardsInfo.objects.create(**reward_info_dict)

        return super().setUp()

    @print_success_message("유효기간이 만료된 쿠폰 템플릿이 표시되지 않는지 테스트")
    def test_coupon_template_list_expired_coupon_template(self):
        """
        유효기간이 만료된 쿠폰 템플릿이 표시되지 않는지 테스트하는 테스트 메소드입니다.
        """

        # 유저 생성 및 로그인
        user= User.objects.create(username='test', password='1234')
        self.client.force_authenticate(user=user)

        # 쿠폰 템플릿 목록 조회
        r = self.client.get('/couponbook/coupon-templates/')
        self.assertEqual(bool(r.data), False, "유효 기간이 만료된 쿠폰 템플릿이 조회되었습니다!")
    
    @print_success_message("유효기간이 만료된 쿠폰 템플릿으로 쿠폰이 등록되지 않는지 테스트")
    def test_add_coupon_from_expired_coupon_template(self):
        """
        쿠폰 템플릿의 유효기간이 만료되었을 때, 쿠폰이 등록되지 않는지 테스트하는 테스트 메소드입니다.
        """

        # 유저 생성 및 로그인
        user = User.objects.create(username='test', password='1234')
        self.client.force_authenticate(user=user)

        # 쿠폰 등록
        r = self.client.post('/couponbook/couponbooks/1/coupons/', {'original_template': 1})
        self.assertEqual(r.status_code, 400, "쓸모없는 쿠폰이 등록되었습니다!")

class FullCouponTemplateTestCase(APITestCase):
    """
    쿠폰 템플릿의 선착순 인원이 모두 채워졌을 때, 쿠폰이 등록되지 않는지 테스트하는 테스트 케이스입니다.
    """

    @print_success_message("쿠폰 템플릿의 선착순 인원이 모두 채워졌을 때, 쿠폰이 등록되지 않는지 테스트")
    def test_add_coupon_from_full_coupon_template(self):
        """
        이미 쿠폰 템플릿의 선착순 인원이 마감되었는데, 추가로 쿠폰이 등록되지는 않는지 테스트하는 테스트 메소드입니다.
        """

        # 법정동 주소 생성
        legal_district_dict = {
            'code_in_law': '1123011000',
            'province': '서울특별시',
            'city': '동대문구',
            'district': '이문동',
        }
        legal_district = LegalDistrict.objects.create(**legal_district_dict)
        
        # 가게 생성
        place_dict = {
            'name': '한국외대 서울캠퍼스',
            'address_district': legal_district,
            'address_rest': '1234',
            'image_url': 'aaa.jpg',
            'opens_at': now().time(),
            'closes_at': now().time(),
            'tags': '대학교',
            'last_order': now().time(),
            'tel': '02-xxxx-xxxx',
            'owner': None,
        }
        place = Place.objects.create(**place_dict)

        # 쿠폰 템플릿 생성
        original_template_dict = {
            'valid_until': now() + timedelta(days=5),
            'first_n_persons': 1,
            'is_on': True,
            'place': place
        }
        coupon_template = CouponTemplate.objects.create(**original_template_dict)

        reward_info_dict = {
            'amount': 5,
            'reward': '대학원 무료',
            'coupon_template': coupon_template,
        }
        RewardsInfo.objects.create(**reward_info_dict)

        # 유저 생성
        user1 = User.objects.create(username='test1', password='1234')
        user2 = User.objects.create(username='test2', password='1234')

        # 유저1로 로그인 후 쿠폰 등록
        self.client.force_authenticate(user=user1)
        r = self.client.post('/couponbook/couponbooks/1/coupons/', {'original_template': 1})
        self.assertEqual(r.status_code, 201, "쿠폰 등록에 실패한 것 같습니다...")
        
        # 유저2로 로그인 후 쿠폰 등록 (실패해야 함)
        self.client.force_authenticate(user=user2)
        r = self.client.post('/couponbook/couponbooks/2/coupons/', {'original_template': 1})
        self.assertEqual(r.status_code, 400, "이건 선착순이 아니네요..")

class AlreadyOwnCouponTemplateTestCase(APITestCase):
    """
    이미 등록한 쿠폰 템플릿이 중복 등록되지 않는지 테스트하는 테스트 케이스입니다.
    """

    @print_success_message("이미 등록한 쿠폰 템플릿이 중복 등록되지 않는지 테스트")
    def test_add_coupon_from_already_own_coupon_template(self):
        """
        이미 등록한 쿠폰 템플릿이 중복 등록되지 않는지 테스트하는 테스트 메소드입니다.
        """

        # 법정동 주소 생성
        legal_district_dict = {
            'code_in_law': '1123011000',
            'province': '서울특별시',
            'city': '동대문구',
            'district': '이문동',
        }
        legal_district = LegalDistrict.objects.create(**legal_district_dict)
        
        # 가게 생성
        place_dict = {
            'name': '한국외대 서울캠퍼스',
            'address_district': legal_district,
            'address_rest': '1234',
            'image_url': 'aaa.jpg',
            'opens_at': now().time(),
            'closes_at': now().time(),
            'tags': '대학교',
            'last_order': now().time(),
            'tel': '02-xxxx-xxxx',
            'owner': None,
        }
        place = Place.objects.create(**place_dict)

        # 쿠폰 템플릿 생성
        original_template_dict = {
            'valid_until': now() + timedelta(days=5),
            'first_n_persons': 10,
            'is_on': True,
            'place': place
        }
        coupon_template = CouponTemplate.objects.create(**original_template_dict)

        reward_info_dict = {
            'amount': 5,
            'reward': '대학원 무료',
            'coupon_template': coupon_template,
        }
        RewardsInfo.objects.create(**reward_info_dict)

        # 유저 생성
        user1 = User.objects.create(username='test1', password='1234')
        self.client.force_authenticate(user=user1)

        # 쿠폰 등록
        r = self.client.post('/couponbook/couponbooks/1/coupons/', {'original_template': 1})
        self.assertEqual(r.status_code, 201, "쿠폰 등록에 실패한 것 같습니다..")
        
        r = self.client.post('/couponbook/couponbooks/1/coupons/', {'original_template': 1})
        self.assertEqual(r.status_code, 400, "쿠폰이 복사가 되네요..")
        
class LackRelatedDataTestCase(APITestCase):
    """
    연관성이 있는 데이터 중 한쪽의 데이터가 없을 때 오류가 발생하지 않는지 테스트합니다.
     
    주로 응답 상태 코드를 Assertion하여 문제 없이 한 로직이 작동되는지에 초점을 맞춥니다.
    """

    @print_success_message("리워드 정보가 없을 때에도 쿠폰 템플릿 목록 조회가 오류없이 작동하는지 테스트")
    def test_coupon_template_list_when_lack_reward_info(self):
        """
        쿠폰 템플릿은 reward_info를 역참조합니다. 역참조 데이터가 없을 때 오류가 발생하지 않는지 테스트하는 테스트 메소드입니다.
        """
        # 법정동 주소 생성
        legal_district_dict = {
            'code_in_law': '1123011000',
            'province': '서울특별시',
            'city': '동대문구',
            'district': '이문동',
        }
        legal_district = LegalDistrict.objects.create(**legal_district_dict)
        
        # 가게 생성
        place_dict = {
            'name': '한국외대 서울캠퍼스',
            'address_district': legal_district,
            'address_rest': '1234',
            'image_url': 'aaa.jpg',
            'opens_at': now().time(),
            'closes_at': now().time(),
            'tags': '대학교',
            'last_order': now().time(),
            'tel': '02-xxxx-xxxx',
            'owner': None,
        }
        place = Place.objects.create(**place_dict)

        # 쿠폰 템플릿 생성
        original_template_dict = {
            'first_n_persons': 10,
            'is_on': True,
            'place': place
        }
        CouponTemplate.objects.create(**original_template_dict)

        # 유저 생성 및 로그인
        user = User.objects.create(username='test', password='1234')
        self.client.force_authenticate(user=user)

        # 쿠폰 템플릿 목록 조회
        r = self.client.get('/couponbook/coupon-templates/')
        print(r.status_code)
        self.assertNotEqual(r.status_code, 500, "예외 상황이 제대로 처리되지 않았습니다!")
    
    @print_success_message("리워드 정보가 없을 때에도 쿠폰 목록 조회가 오류없이 작동하는지 테스트")
    def test_coupon_get_when_lack_reward_info(self):
        """
        쿠폰은 reward_info를 필요로 합니다. reward_info가 없을 때 쿠폰을 조회하면 오류가 발생하는지 테스트합니다.
        """

        # 법정동 주소 생성
        legal_district_dict = {
            'code_in_law': '1123011000',
            'province': '서울특별시',
            'city': '동대문구',
            'district': '이문동',
        }
        legal_district = LegalDistrict.objects.create(**legal_district_dict)
        
        # 가게 생성
        place_dict = {
            'name': '한국외대 서울캠퍼스',
            'address_district': legal_district,
            'address_rest': '1234',
            'image_url': 'aaa.jpg',
            'opens_at': now().time(),
            'closes_at': now().time(),
            'tags': '대학교',
            'last_order': now().time(),
            'tel': '02-xxxx-xxxx',
            'owner': None,
        }
        place = Place.objects.create(**place_dict)

        # 쿠폰 템플릿 생성
        original_template_dict = {
            'first_n_persons': 10,
            'is_on': True,
            'place': place
        }
        CouponTemplate.objects.create(**original_template_dict)

        # 유저 생성 및 로그인
        user = User.objects.create(username='test', password='1234')
        self.client.force_authenticate(user=user)

        # 쿠폰 등록
        r = self.client.post('/couponbook/couponbooks/1/coupons/', {'original_template': 1})
        self.assertEqual(r.status_code, 201, "쿠폰 등록에 실패한 것 같습니다...")

        # 쿠폰 목록 조회
        r = self.client.get('/couponbook/couponbooks/1/coupons/')
        self.assertNotEqual(r.status_code, 500, "예외 상황이 제대로 처리되지 않았습니다!")

        # 단일 쿠폰 조회
        r = self.client.get('/couponbook/coupons/1/')
        self.assertNotEqual(r.status_code, 500, "예외 상황이 제대로 처리되지 않았습니다!")
