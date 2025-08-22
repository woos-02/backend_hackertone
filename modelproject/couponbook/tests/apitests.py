from datetime import datetime

from accounts.models import User
from couponbook.models import *
from django.test import TestCase
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
            'opens_at': datetime.now().time(),
            'closes_at': datetime.now().time(),
            'tags': '대학교',
            'last_order': datetime.now().time(),
            'tel': '02-xxxx-xxxx',
            'owner': None,
        }
        place = Place.objects.create(**place_dict)

        # 쿠폰 템플릿 생성
        original_template_dict = {
            'valid_until': datetime.now(),
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
        self.assertEqual(r.data['favorite_counts'], 1, f"예상된 즐겨찾기 쿠폰 개수와 다릅니다. ({r.data['favorite_counts']}, 1)")
        
        # 즐겨찾기 쿠폰 삭제
        self.client.delete('/couponbook/own-couponbook/favorites/1/')
        r = self.client.get('/couponbook/own-couponbook/')
        self.assertEqual(r.data['favorite_counts'], 0, f"예상된 즐겨찾기 쿠폰 개수와 다릅니다. ({r.data['favorite_counts']}, 0)")
        

class ResponseTestCase(APITestCase):
    """
    필요한 데이터를 반환하고 있는지 테스트하는 테스트 케이스입니다.
    """

    pass