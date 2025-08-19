from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User
from couponbook.models import CouponBook


@receiver(post_save, sender=User)
def create_coupon_book(sender, instance, created, **kwargs):
    """
    새로운 User 객체가 생성된 후(post_save), 해당 사용자가 손님(customer)인 경우
    couponbook을 자동으로 생성하는 시그널 핸들러입니다.

    Args:
        sender (Model): 시그널을 보낸 모델. 여기서는 User 모델입니다.
        instance (User): 방금 생성되거나 업데이트된 User 인스턴스입니다.
        created (bool): 새로운 객체가 생성되었을 때 True입니다.
        **kwargs: 추가적인 키워드 인수입니다.

    Returns:
        None
    """
    # 사용자가 방금 생성되었고, 역할이 'customer'인 경우에만 실행됩니다.
    if created and instance.is_customer():
        # CouponBook 인스턴스를 생성하고, 외래키(ForeignKey) 필드에 새로 생성된 user를 할당
        try:
            CouponBook.objects.create(user=instance)

        except Exception as e:
            # 예외가 발생하면 로깅을 남겨 디버깅에 도움
            print(f"Error creating CouponBook for user {instance.username}: {e}")