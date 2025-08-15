from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Receipt, Stamp


@receiver(post_save, sender=Stamp)
def stamp_create_callback(sender: Stamp, **kwargs):
    """
    스탬프가 생성되었을 때, 영수증 인스턴스에 스탬프를 연결하는 콜백 함수입니다.
    """
    # 생성되었을 때가 아니므로 리턴함
    if not kwargs.get('created'):
        return
    
    stamp: Stamp = kwargs.get('instance')
    receipt: Receipt = Receipt.objects.get(receipt_number=stamp.receipt_number)
    receipt.stamp = stamp
    receipt.save()