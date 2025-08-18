from django.apps import AppConfig


class CouponbookConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'couponbook'

    def ready(self):
        from . import signals