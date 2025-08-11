from django.db import models

# Create your models here.
class PaymentHistory(models.Model):
    customer = models.ForeignKey("accounts.models.User",
                                 on_delete=models.CASCADE,
                                 help_text="구매하는 고객입니다.")
    order_number = models.CharField(help_text="주문 번호입니다.")
    pay_amount = models.PositiveIntegerField(help_text="결제 금액입니다.")