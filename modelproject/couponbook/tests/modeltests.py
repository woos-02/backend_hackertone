from datetime import datetime

from accounts.models import User
from couponbook.models import *
from django.test import TestCase
from django.utils.timezone import now

from .decorators import print_success_message


# 모델 관련 테스트케이스
# 쿠폰북 관련 테스트케이스
class CouponBookTestCase(TestCase):
    # 유저 생성 시 연관된 쿠폰북 생기는지?
    @print_success_message("유저 생성 시 연관된 쿠폰북 생성 테스트")
    def test_user_with_couponbook(self):
        user = User.objects.create(username='test', password='1234')
        self.assertEqual(CouponBook.objects.filter(user=user).exists(), True)


class CouponTestCase(TestCase):
    def setUp(self):
        """
        쿠폰 관련 테스트를 진행하기 전, 각 테스트 전에 실행되어 미리 필요한 데이터를 생성합니다.
        """
        # 유저 생성
        user = User.objects.create(username='test', password='1234')
        
        # 법정동 주소 생성
        legal_district_dict = {
            'code_in_law': '00000001',
            'province': '서울',
            'city': '구',
            'district': '서남북동',
        }
        legal_district = LegalDistrict.objects.create(**legal_district_dict)
        
        now_date = now()
        now_time = datetime.now().time()
        
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
        original_template = CouponTemplate.objects.create(**original_template_dict)

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
