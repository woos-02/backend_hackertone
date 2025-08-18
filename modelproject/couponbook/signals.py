from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Receipt, Stamp


@receiver(post_save, sender=Stamp)
def stamp_create_callback(sender: Stamp, **kwargs):
    return

@receiver(post_delete, sender=Stamp)
def stamp_delete_callback(sender: Stamp, **kwargs):
    return