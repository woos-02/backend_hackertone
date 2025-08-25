from accounts.models import User
from couponbook.curation.utils import AICurator, UserStatistics
from couponbook.models import *
from django.utils.timezone import now
from rest_framework.test import APITestCase

from .decorators import print_success_message

# 큐레이터와 유저 통계 관련 테스트케이스

class CuratorTestCase(APITestCase):
    """
    큐레이터의 동작을 테스트하는 테스트 케이스입니다.
    """

    def setUp(self):
        # 유저 생성
        User.objects.create(username='test', password='1234')

        return super().setUp()

    @print_success_message("유저 통계가 제대로 생성되는지 테스트")
    def test_generate_user_statistics(self):
        """
        유저 통계가 오류 없이 생성되는지 테스트하는 테스트 메소드입니다.
        """
        
        # 통계 만들기
        UserStatistics(user=User.objects.get(id=1)).make_history()

        # 오류 없으면 테스트 통과!

    @print_success_message("쿠폰 템플릿 없이 큐레이션 진행 테스트")
    def test_curation_without_any_coupon_templates(self):
        """
        쿠폰 템플릿을 하나도 생성하지 않고 테스트를 진행했을 때, 오류 없이 큐레이션이 진행되는지 테스트합니다.
        """

        s = UserStatistics(user=User.objects.get(id=1))
        a = AICurator()
        t = CouponTemplate.objects.filter(is_on=True)
        result = a.curate(s, t)
        self.assertEqual(result, [], "메소드의 반환값이 예상되는 값과 다릅니다.")
        

    @print_success_message("쿠폰 템플릿이 3개 이하일 경우 테스트")
    def test_less_than_or_equal_three_coupon_templates_curation(self):
        """
        쿠폰 템플릿이 3개 이하일 경우, 모든 쿠폰 템플릿 id가 반환되는지 테스트하는 테스트 메소드입니다.

        아래의 경우 쿠폰 템플릿이 1개입니다.
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

        s = UserStatistics(user=User.objects.get(id=1))
        a = AICurator()
        t = CouponTemplate.objects.filter(is_on=True)

        result = a.curate(s, t)
        print(result)
        self.assertEqual(len(result), 1, "귀신이 쿠폰 템플릿을 추가하거나 삭제했나봐요..")
    
    @print_success_message("이미 보유한 쿠폰이 추천되지 않는지 테스트")
    def test_no_curation_for_already_owned_coupon(self):
        """
        이미 보유한 쿠폰 템플릿이 추천되지 않는지 테스트하는 테스트 메소드입니다.
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

        reward_info_dict = {
            'amount': 5,
            'reward': '대학원 무료',
            'coupon_template': coupon_template,
        }
        RewardsInfo.objects.create(**reward_info_dict)

        # API 클라이언트 통해서 쿠폰 큐레이션 실행
        self.client.force_authenticate(user=User.objects.get(id=1))
        r = self.client.get('/couponbook/own-couponbook/curation/')
        self.assertEqual(len(r.data), 1, "귀신이 쿠폰 템플릿을 추가하거나 삭제했나봐요..")

        # 쿠폰 등록 후 큐레이션 재실행
        self.client.post('/couponbook/couponbooks/1/coupons/', {'original_template': 1})
        r = self.client.get('/couponbook/own-couponbook/curation/')
        self.assertEqual(len(r.data), 0, "이미 보유하고 있는 쿠폰 템플릿이 추천되어 버렸습니다...")
