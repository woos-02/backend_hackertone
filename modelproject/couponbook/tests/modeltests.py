from accounts.models import User
from couponbook.latlng.utils import KakaoMapAPIClient
from couponbook.models import *
from django.test import TestCase
from django.utils.timezone import now, timedelta

from .decorators import print_success_message


# 모델 관련 테스트케이스
class CouponBookTestCase(TestCase):
    """
    쿠폰북 모델 관련 테스트 케이스입니다.
    """

    @print_success_message("유저 생성 시 연관된 쿠폰북 생성 테스트")
    def test_user_with_couponbook(self):
        """
        유저를 생성할 때 유저의 쿠폰북이 자동으로 생성되는지 테스트하는 테스트 메소드입니다.
        """
        
        user = User.objects.create(username='test', password='1234')
        self.assertEqual(CouponBook.objects.filter(user=user).exists(), True)

class CouponTestCase(TestCase):
    """
    쿠폰 모델 관련 테스트 케이스입니다.
    """

    def setUp(self):
        """
        쿠폰 관련 테스트를 진행하기 전, 각 테스트 전에 실행되어 미리 필요한 데이터를 생성합니다.
        """

        # 유저 생성
        user = User.objects.create(username='test', password='1234')
        
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
        original_template = CouponTemplate.objects.create(**original_template_dict)

        # 리워드 정보 생성
        reward_info_dict = {
            'amount': 5,
            'reward': '대학원 무료',
            'coupon_template': original_template,
        }
        RewardsInfo.objects.create(**reward_info_dict)

        # 테스트에서 활용할 인스턴스들을 딕셔너리에 담아서 저장
        self.test_context = {
            'user': user,
            'couponbook': CouponBook.objects.get(user=user),
            'original_template': original_template,
        }

        return super().setUp()
    
    # 존재하는 쿠폰 삭제하였을 경우 영수증 데이터와 스탬프 연결 해제되는지?
    @print_success_message("존재하는 쿠폰 삭제 시 영수증 데이터와 스탬프 연결 해제 테스트")
    def test_coupon_delete_and_receipts_and_stamps(self):
        """
        존재하는 쿠폰을 삭제했을 때, 영수증 데이터와 스탬프의 연결이 해제되는지 테스트하는 테스트 메소드입니다.
        """
        
        user, couponbook, original_template = self.test_context.values()
        
        # 쿠폰 생성
        coupon_dict = {
            'couponbook': couponbook,
            'original_template': original_template,
        }
        coupon = Coupon.objects.create(**coupon_dict)

        # 영수증 생성
        receipt_dict = {
            'receipt_number': '000000001'
        }
        receipt = Receipt.objects.create(**receipt_dict)

        # 스탬프 적립
        stamp_dict = {
            'coupon': coupon,
            'receipt': receipt,
            'customer': user,
        }
        stamp = Stamp.objects.create(**stamp_dict)

        # 1. 영수증 - 스탬프 연동 테스트
        self.assertEqual(receipt.stamp, stamp)

        # 2. 쿠폰 - 스탬프 연동 테스트
        self.assertEqual(coupon.stamps.exists(), True)

        # 3. 쿠폰 삭제
        coupon.delete()
        
        # 4. 영수증을 다시 불러옴
        receipt = Receipt.objects.get(receipt_number=receipt_dict['receipt_number'])
        
        # 5. 영수증 - 스탬프 연동 해제 테스트
        self.assertEqual(hasattr(receipt, 'stamp'), False, "영수증과 연결된 스탬프가 남아있음!")

class PlaceTestCase(TestCase):
    def setUp(self):
        legal_district_1 = {
            'code_in_law': '1114011100',
            'province': '서울특별시',
            'city': '중구',
            'district': '소공동',
        }
        legal_district_2 = {
            'code_in_law': '1117010500',
            'province': '서울특별시',
            'city': '용산구',
            'district': '남영동',
        }
        legal_district_3 = {
            'code_in_law': '4111710100',
            'province': '경기도',
            'city': '수원시영통구',
            'district': '매탄동',
        }

        LegalDistrict.objects.create(**legal_district_1)
        LegalDistrict.objects.create(**legal_district_2)
        LegalDistrict.objects.create(**legal_district_3)

    @print_success_message("가게 등록 시 가게의 위도, 경도를 제대로 저장하는지 확인 테스트")
    def test_place_lat_and_lng(self):
        """
        가게를 등록할 때, 가게의 위도, 경도가 제대로 저장되는지 확인하는 테스트 메소드입니다.
        """
        
        legal_district = LegalDistrict.objects.get(code_in_law='1114011100')

        place_dict = {
            'name': '서울역',
            'address_district': legal_district,
            'address_rest': '1234',
            'image_url': 'aaa.jpg',
            'opens_at': now().time(),
            'closes_at': now().time(),
            'tags': '역',
            'last_order': now().time(),
            'tel': '02-xxxx-xxxx',
            'owner': None,
        }
        place = Place.objects.create(**place_dict)
        lat, lng = place.lat, place.lng

        client = KakaoMapAPIClient()
        kakaomap_place = client.find_place_by_keyword("서울역")
        t_lat, t_lng = kakaomap_place.get_latlng()
        
        self.assertEqual((lat, lng), (t_lat, t_lng))

    @print_success_message("가게 등록 시 없는 가게 이름으로 가게를 등록하는 경우의 예외 처리 테스트")
    def test_false_place_lat_and_lng(self):
        """
        가게를 등록할 때, 없는 가게 이름으로 가게를 등록하는 경우, 가게가 등록되지 않는지 테스트하는 테스트 메소드입니다.
        """
        
        legal_district = LegalDistrict.objects.get(code_in_law='1117010500')
        place_dict = {
            'name': '디즈니랜드',
            'address_district': legal_district,
            'address_rest': '1234',
            'image_url': 'aaa.jpg',
            'opens_at': now().time(),
            'closes_at': now().time(),
            'tags': '역',
            'last_order': now().time(),
            'tel': '02-xxxx-xxxx',
            'owner': None,
        }

        place = Place.objects.create(**place_dict)
        self.assertTrue(isinstance(place, Place), "예외 처리가 제대로 되지 않았음!")
    
    @print_success_message("가게 등록 시 이름이 중복된 가게의 위도, 경도가 제대로 처리되는지 테스트")
    def test_not_unique_place_name_lat_lng(self):
        """
        가게를 등록할 때, 이름이 중복된 가게가 있을 수 있습니다.

        이 경우에도 주소에 따라 이름이 중복된 가게의 위도, 경도가 제대로 처리되는지 테스트하는 테스트 메소드입니다.
        """
        
        # 키워드 군포해물탕 vs 군포해물탕 영통 위도와 경도 비교
        legal_district = LegalDistrict.objects.get(code_in_law='4111710100')
        place_dict = {
            'name': '군포해물탕',
            'address_district': legal_district,
            'address_rest': '1234',
            'image_url': 'aaa.jpg',
            'opens_at': now().time(),
            'closes_at': now().time(),
            'tags': '식당',
            'last_order': now().time(),
            'tel': '02-xxxx-xxxx',
            'owner': None,
        }
        place = Place.objects.create(**place_dict)
        lat, lng = place.lat, place.lng

        client = KakaoMapAPIClient()
        kakaomap_place = client.find_place_by_keyword("군포해물탕 영통")
        t_lat, t_lng = kakaomap_place.get_latlng()

        # place의 예상되는 위도, 경도: place의 address_district 정보를 추가로 활용해서 검색된 값
        self.assertEqual((lat, lng), (t_lat, t_lng), f"예상된 값과 위도와 경도가 다름: ({(t_lat, t_lng)})")
