from accounts.models import User
from django.test import TestCase
from rest_framework.test import APITestCase

from .decorators import print_success_message


# API(뷰) 관련 테스트 케이스
class CouponBookViewTestCase(APITestCase):
    """
    쿠폰북 뷰 관련
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
        self.assertEqual(r2_user1.status_code, 401) # 남의 쿠폰들이므로 401

        # user2로 로그인
        self.client.force_authenticate(user=user2)
        r1_user2 = self.client.get('/couponbook/couponbooks/1/coupons/')
        self.assertEqual(r1_user2.status_code, 401) # 남의 쿠폰들이므로 401
        r2_user2 = self.client.get('/couponbook/couponbooks/2/coupons/')
        self.assertEqual(r2_user2.status_code, 200) # 본인의 쿠폰들이므로 200
