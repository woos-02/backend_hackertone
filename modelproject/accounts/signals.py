from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User
from couponbook.models import CouponBook


@receiver(post_save, sender=User)
def create_coupon_book(sender, instance, created, **kwargs):
    """
    새로운 User 객체가 생성될 때, 해당 사용자가 손님(CUSTOMER)인 경우에만
    CouponBook을 자동으로 생성하는 시그널 핸들러입니다.
    """
    if created and instance.is_customer():
        # CouponBook 인스턴스를 생성하고, 외래키(ForeignKey) 필드에 새로 생성된 user를 할당
        try:
            CouponBook.objects.create(user=instance)

        except Exception as e:
            # 예외가 발생하면 로깅을 남겨 디버깅에 도움
            print(f"Error creating CouponBook for user {instance.username}: {e}")